import modal


cache_dir = "/data"
volume = modal.Volume.from_name("embedding-wikipedia-weaviate", create_if_missing=True)

image = modal.Image.debian_slim(python_version="3.11").pip_install("datasets")


def generate_batches(xs, batch_size=512):
    """Batches an input `xs` by yielding sublists of size `batch_size` from it."""
    batch = []
    for x in xs:
        batch.append(x)
        if len(batch) == batch_size:
            yield batch
            batch = []
    if batch:
        yield batch
