import time

import modal

image = modal.Image.debian_slim(python_version="3.11").pip_install(
    "weaviate-client==4.5.4", "fastapi==0.110.1"
)
app = modal.App(
    "modal-weaviate", image=image, secrets=[modal.Secret.from_name("wiki-weaviate")]
)

REPORT_INSERT = 5120

VECTOR_INDEX_PARAMS = {
    # graph parameter: maximum number of connections per element
    "max_connections": 16,
    # efficiency factor: how many elements to consider as candidate neighbors during queries
    "ef": 16,
    # efficiency factor at construction: same as ef, but for the initial construction of the index
    "ef_construction": 32,
}

with image.imports():
    import weaviate
    import weaviate.classes as wvc
    import os

MINUTES = 60
HOURS = 60 * MINUTES

COLLECTION_NAME = "Wikipedia"


@app.cls(
    concurrency_limit=8,
    timeout=12 * HOURS,
    container_idle_timeout=5 * MINUTES,
    cpu=1,  # 4x over-provisioned
    memory=2048,  # 4x over-provisioned
)
class WeaviateClient:
    @modal.enter()
    def connect(self):
        weaviate_api_key = os.getenv("WCS_ADMIN_KEY")
        if weaviate_api_key is None:
            weaviate_api_key = os.getenv("WCS_RO_KEY")
            if weaviate_api_key is None:
                raise ValueError(
                    "🧶: WCS_ADMIN_KEY or WCS_RO_KEY must be set in wiki-weaviate secret"
                )
            else:
                print("🧶: using read-only Weaviate key")
        self.client = weaviate.connect_to_wcs(
            os.environ["WCS_URL"],
            weaviate.auth.AuthApiKey(weaviate_api_key),
            additional_config=weaviate.config.AdditionalConfig(
                timeout=(10 * MINUTES, 10 * MINUTES)
            ),
            skip_init_checks=True,
        )
        return self.client

    @modal.exit()
    def close(self):
        self.client.close()

    @modal.method()
    def check_connection(self):
        if self.client.is_ready():
            print("🧶: Weaviate is ready")
            return True
        return False

    @modal.method()
    def create_collection(self, wipe: bool = False):
        client = self.client
        print("🧶: connected to Weaviate")

        if client.collections.exists(COLLECTION_NAME) and not wipe:
            print(
                f"🧶: collection {COLLECTION_NAME} already exists. Set wipe to True to delete and recreate it."
            )
        else:
            if wipe:
                print(f"🧶: deleting existing collection {COLLECTION_NAME}")
                client.collections.delete(COLLECTION_NAME)
                wait, backoff = 5, 1.25
                while client.collections.exists(COLLECTION_NAME):
                    print("🧶: waiting for collection to be deleted")
                    time.sleep(wait)
                    wait *= backoff
                print("🧶: collection deleted")
            print(f"🧶: creating collection {COLLECTION_NAME}")
            client.collections.create(
                COLLECTION_NAME,
                vectorizer_config=wvc.config.Configure.Vectorizer.none(),
                vector_index_config=wvc.config.Configure.VectorIndex.hnsw(
                    distance_metric=wvc.config.VectorDistances.L2_SQUARED,
                    quantizer=wvc.config.Configure.VectorIndex.Quantizer.pq(
                        training_limit=50000
                    ),
                    **VECTOR_INDEX_PARAMS,
                ),
                inverted_index_config=wvc.config.Configure.inverted_index(
                    index_timestamps=False
                ),
                properties=[
                    wvc.config.Property(
                        name="identifier",
                        data_type=wvc.config.DataType.INT,
                    ),
                    wvc.config.Property(
                        name="chunk_index",
                        data_type=wvc.config.DataType.INT,
                    ),
                    wvc.config.Property(
                        name="content",
                        data_type=wvc.config.DataType.TEXT,
                        index_filterable=False,
                        index_searchable=False,
                    ),
                    wvc.config.Property(
                        name="url",
                        data_type=wvc.config.DataType.TEXT,
                        index_filterable=False,
                        index_searchable=False,
                    ),
                    wvc.config.Property(
                        name="title",
                        data_type=wvc.config.DataType.TEXT,
                        index_filterable=True,
                        index_searchable=True,
                    ),
                ],
            )

        assert client.collections.exists(
            COLLECTION_NAME
        ), f"Error creating collection {COLLECTION_NAME}"

        print(f"🧶: collection {COLLECTION_NAME} available")

    @modal.method()
    def insert(self, metadata, vectors):
        client = self.client

        collection = client.collections.get(COLLECTION_NAME)

        print(f"🧶: inserting {len(metadata)} rows into {COLLECTION_NAME} collection")
        ct = 0
        start = time.perf_counter()
        with collection.batch.fixed_size(1024) as batch:
            for md, v in zip(metadata, vectors):
                batch.add_object(properties=md, vector=v)
                ct += 1
                if (ct % REPORT_INSERT) == 0:
                    duration = time.perf_counter() - start
                    print(
                        f"🧶: inserted {ct} rows into {COLLECTION_NAME} collection in {int(duration) if duration > 1 else round(duration, 2)}s, throughput {int(ct / duration)} rows/s"
                    )

        print(f"🧶: finished inserting data into {COLLECTION_NAME} collection")

    @modal.method()
    def get_node_info(self):
        nodes_info = self.client.cluster.nodes(
            collection=COLLECTION_NAME,
            output="verbose",
        )
        print("🧶: Weaviate node info", *nodes_info, sep="\n\t")
        return str(nodes_info)

    @modal.method()
    def query(self, q: str):
        client = self.client

        collection = client.collections.get(COLLECTION_NAME)

        print(f"🧶: querying {COLLECTION_NAME} collection for '{q}'")
        bm25results = collection.query.bm25(
            query=q,
            query_properties=["title"],
            limit=10,
            include_vector=True,
        )
        print(f"🧶: BM25 found {len(bm25results.objects)} results")

        title_results = collection.query.fetch_objects(
            filters=wvc.query.Filter.by_property("title").equal(q),
            sort=wvc.query.Sort.by_property(name="chunk_index", ascending=True),
            include_vector=True,
        )

        print(f"🧶: title match found {len(title_results.objects)} results")

        if title_results.objects:
            results = title_results
        else:
            results = bm25results

        return [
            obj.properties | {"vector": obj.vector["default"]}
            for obj in results.objects
        ]

    @modal.method()
    def query_vector(self, vector: [float]):
        client = self.client

        collection = client.collections.get(COLLECTION_NAME)

        print(
            f"🧶: querying vector [{vector[0]}, {vector[1]}, {vector[2]}...] against {COLLECTION_NAME} collection"
        )
        results = collection.query.near_vector(
            near_vector=vector, limit=1, include_vector=False
        )
        print(f"🧶: found {len(results.objects)} results")

        return [obj.properties for obj in results.objects]

    @modal.method()
    def total_count(self):
        result = self.client.collections.get(COLLECTION_NAME).aggregate.over_all(
            total_count=True
        )
        return result.total_count


@app.function(keep_warm=1)
@modal.web_endpoint()
def query(q: str) -> dict:
    results = WeaviateClient().query.remote(q)
    return {"results": results}


@app.function(keep_warm=1)
@modal.web_endpoint(method="POST")
def vector(data: dict) -> dict:
    vector = data["vector"]
    results = WeaviateClient().query_vector.remote(vector)
    print("🧶: vector query reutrned results")
    print(results)
    return {"results": results}


@app.local_entrypoint()
def main(wipe: bool = False):
    """Creates the collection if it doesn't exist, wiping it first if requested.

    Note that this script can only be run if the `WCS_ADMIN_KEY` is set in the `wiki-weaviate` secret.

    Run this function with `modal run database.py`."""
    WeaviateClient().create_collection.remote(wipe=wipe)
