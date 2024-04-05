import modal


cache_dir = "/data"
volume = modal.Volume.persisted("embedding-wikipedia-wcs")

image = modal.Image.debian_slim().pip_install("datasets")


def generate_batches(xs, batch_size=512):
    batch = []
    for x in xs:
        batch.append(x)
        if len(batch) == batch_size:
            yield batch
            batch = []
    if batch:
        yield batch
