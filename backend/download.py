import modal

from .common import cache_dir, volume, image

app = modal.App(image=image)

with image.imports():
    import datasets


@app.function(volumes={cache_dir: volume}, timeout=3000)
def download_dataset(cache=False):
    # Download and save the dataset locally on Modal worker
    dataset = datasets.load_dataset(
        "wikipedia", "20220301.en", num_proc=10, trust_remote_code=True
    )
    dataset.save_to_disk(f"{cache_dir}/wikipedia")

    # commit changes so they are visible to other Modal functions
    volume.commit()
