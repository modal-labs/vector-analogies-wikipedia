# Vector Analogies on Wikipedia
### Powered by [Modal](https://modal.com) & [Weaviate](https://weaviate.io)

## What is this for?

This is a sample project that shows how to combine the serverless infrastructure of [Modal](https://modal.com)
with the search capabilities of [Weaviate](https://weaviate.io)
for projects that combine data-intensive Python compute, like neural network inference,
with data-intensive storage, like storing all of Wikipedia.

It's intended as starter code, and it supports a [live demo application](https://vector-analogies-wikipedia.vercel.app/).

## What does it do?

The `frontend` of this project (written in React, hosted on [Vercel](https://vercel.com))
allows users to construct "vector analogies" of the form made famous by [Word2Vec](https://arxiv.org/abs/1301.3781):

```
Paris - France + England ~= London
```

but extended to snippets of English Wikipedia articles.
The dataset used was constructed from the March 2022 WikiMedia dump [by Hugging Face](https://huggingface.co/datasets/wikipedia).

Users can type to find a snippet of interest, using Weaviate text search under the hood,
and once they've selected the three components of their analogy,
the frontend kicks off an approximate nearest-neighbor vector search to complete it.

Both searches are coordinated by a `backend` Python service running on Modal.

Modal is also used to construct embeddings for snippets and then insert them into Weaviate.
You can read more about the embedding process [here](https://modal.com/blog/embedding-wikipedia).

## How is it set up?

Because this is a demo and example, rather than a portable artifact,
it's not intended to be easy for anyone else to run.

But here's a rough outline of the configuration and setup:

1. Set up a Python environment and `pip install modal`.
1. Set up a Weaviate database, e.g. via [Weaviate Cloud Services](https://weaviate.io/developers/weaviate/installation/weaviate-cloud-services).
1. Add your `WCS_URL` and `WCS_ADMIN` key to a [`modal.Secret`](https://modal.com/docs/guide/secrets) called `modal-weaviate`.
1. Run `modal deploy backend.database` to create a (serverless, aka free when not in use) database client on Modal.
1. To embed the dataset and send the results to Weaviate, run `modal run backend.ingest`. This can take several hours. Use the `--down-scale` option to reduce the fraction of the data you ingest. 10% is enough to get fair results.
1. Set the URL in the `WeaviateService` in the `frontend` to point at your `WeaviateClient` on Modal.
1. Run a hot-reloading local version of the frontend with `npm run dev`, so you can play around with it.
1. Host the frontend somewhere, e.g. Vercel.
