from huggingface_hub import snapshot_download

snapshot_download(
    repo_id="shi-labs/Agriculture-Vision",
    repo_type="dataset",
    local_dir="agri_dataset"
)