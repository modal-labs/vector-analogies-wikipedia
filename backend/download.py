import modal

from common import cache_dir, volume, image

stub = modal.Stub(image=image)

with image.imports():
    import datasets


@stub.function(volumes={cache_dir: volume}, timeout=3000)
def download_dataset(cache=False):

    # Download and save the dataset locally on Modal worker
    dataset = datasets.load_dataset("wikipedia", "20220301.en", num_proc=10, trust_remote_code=True)
    dataset.save_to_disk(f"{cache_dir}/wikipedia")

    # Commit and save to the shared volume
    volume.commit()
