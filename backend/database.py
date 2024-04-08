import time

import modal

image = modal.Image.debian_slim().pip_install(
    "weaviate-client==4.5.4", "fastapi==0.110.1"
)
stub = modal.Stub(
    "modal-weaviate", image=image, secrets=[modal.Secret.from_name("wikipedia-wcs")]
)

REPORT_INSERT = 5120

VECTOR_INDEX_PARAMS = {
    # graph parameter: maximum number of connections per element
    "max_connections": 32,
    # efficiency factor: how many elements to consider as candidate neighbors during queries
    "ef": 32,
    # efficiency factor at construction: same as ef, but for the initial construction of the index
    "ef_construction": 64,
}

with image.imports():
    import weaviate
    import weaviate.classes as wvc
    import os

MINUTES = 60
HOURS = 60 * MINUTES


@stub.cls(
    concurrency_limit=8,
    timeout=12 * HOURS,
    container_idle_timeout=60,
    cpu=1,  # 4x over-provisioned
    memory=2048,  # 2x over-provisioned
)
class WeaviateClient:
    @modal.enter()
    def connect(self):
        self.client = weaviate.connect_to_wcs(
            os.getenv("WCS_URL"),
            weaviate.auth.AuthApiKey(os.getenv("WCS_ADMIN_KEY")),
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

        if client.collections.exists("Wikipedia") and not wipe:
            print(
                "🧶: collection for Wikipedia already exists. Set wipe to True to delete and recreate it."
            )
        else:
            if wipe:
                print("🧶: deleting existing collection for Wikipedia")
                client.collections.delete("Wikipedia")
                wait, backoff = 5, 1.25
                while client.collections.exists("Wikipedia"):
                    print("🧶: waiting for collection to be deleted")
                    time.sleep(wait)
                    wait *= backoff
                print("🧶: collection for Wikipedia deleted")
            print("🧶: creating collection for Wikipedia")
            client.collections.create(
                "Wikipedia",
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
                        index_filterable=False,
                        index_searchable=True,
                    ),
                ],
            )

        assert client.collections.exists(
            "Wikipedia"
        ), "Error creating collection for Wikipedia"

        print("🧶: collection for Wikipedia available")

    @modal.method()
    def insert(self, metadata, vectors):
        client = self.client
        print("🧶: connected to Weaviate")

        collection = client.collections.get("Wikipedia")

        print(f"🧶: inserting {len(metadata)} rows into Wikipedia collection")
        ct = 0
        start = time.perf_counter()
        with collection.batch.fixed_size(1024) as batch:
            for md, v in zip(metadata, vectors):
                batch.add_object(properties=md, vector=v)
                ct += 1
                if (ct % REPORT_INSERT) == 0:
                    duration = time.perf_counter() - start
                    print(
                        f"🧶: inserted {ct} rows into Wikipedia collection in {int(duration) if duration > 1 else round(duration, 2)}s, throughput {int(ct / duration)} rows/s"
                    )

        print("🧶: finished inserting data into Wikipedia collection")

    @modal.method()
    def get_node_info(self):
        nodes_info = self.client.cluster.nodes(
            collection="Wikipedia",
            output="verbose",
        )
        print("🧶: Weaviate node info", *nodes_info, sep="\n\t")
        return str(nodes_info)

    @modal.method()
    def query(self, q: str):
        client = self.client
        print("🧶: connected to Weaviate")

        collection = client.collections.get("Wikipedia")

        print(f"🧶: querying Wikipedia collection for '{q}'")
        results = collection.query.bm25(
            query=q,
            query_properties=["title"],
            limit=5,
            include_vector=True,
        )
        print(f"🧶: found {len(results.objects)} results")

        return [
            obj.properties | {"vector": obj.vector["default"]}
            for obj in results.objects
        ]

    @modal.method()
    def query_vector(self, vector: [float]):
        client = self.client
        print("🧶: connected to Weaviate")

        collection = client.collections.get("Wikipedia")

        print(
            f"🧶: querying vector [{vector[0]}, {vector[1]}, {vector[2]}...] against Wikipedia collection"
        )
        results = collection.query.near_vector(
            near_vector=vector, limit=1, include_vector=False
        )
        print(f"🧶: found {len(results.objects)} results")

        return [obj.properties for obj in results.objects]

    @modal.method()
    def total_count(self):
        result = self.client.collections.get("Wikipedia").aggregate.over_all(
            total_count=True
        )
        return result.total_count


@stub.function(keep_warm=1)
@modal.web_endpoint()
def query(q: str) -> dict:
    results = WeaviateClient().query.remote(q)
    return {"results": results}


@stub.function(keep_warm=1)
@modal.web_endpoint(method="POST")
def vector(data: dict) -> dict:
    vector = data["vector"]
    results = WeaviateClient().query_vector.remote(vector)
    print(results)
    return {"results": results}


@stub.local_entrypoint()
def main(wipe: bool = False):
    """Creates the collection if it doesn't exist, wiping it first if requested.

    Run this function with `modal run database.py`."""
    WeaviateClient().create_collection.remote(wipe=wipe)
