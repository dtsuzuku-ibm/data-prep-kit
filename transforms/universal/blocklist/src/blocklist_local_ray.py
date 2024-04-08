import os
import sys

from blocklist_transform import (
    BlockListTransformConfiguration,
    annotation_column_name_cli_param,
    blocked_domain_list_path_cli_param,
    source_url_column_name_cli_param,
)
from data_processing.ray import TransformLauncher
from data_processing.utils import ParamsUtils


# create parameters
input_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), "../test-data/input"))
output_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), "../output"))
local_conf = {
    "input_folder": input_folder,
    "output_folder": output_folder,
}

blocklist_conf_url = os.path.abspath(os.path.join(os.path.dirname(__file__), "../test-data/domains"))
blocklist_annotation_column_name = "blocklisted"
blocklist_doc_source_url_column = "title"

block_list_params = {
    blocked_domain_list_path_cli_param: blocklist_conf_url,
    annotation_column_name_cli_param: blocklist_annotation_column_name,
    source_url_column_name_cli_param: blocklist_doc_source_url_column,
}
worker_options = {"num_cpus": 0.8}
code_location = {"github": "github", "commit_hash": "12345", "path": "path"}
launcher_params = {
    # where to run
    "run_locally": True,
    # Data access. Only required parameters are specified
    "data_local_config": ParamsUtils.convert_to_ast(local_conf),
    # orchestrator
    "worker_options": ParamsUtils.convert_to_ast(worker_options),
    "num_workers": 5,
    "pipeline_id": "pipeline_id",
    "job_id": "job_id",
    "creation_delay": 0,
    "code_location": ParamsUtils.convert_to_ast(code_location),
}

# launch
if __name__ == "__main__":
    # Run the transform inside Ray
    # Create the CLI args as will be parsed by the launcher
    sys.argv = ParamsUtils.dict_to_req(launcher_params | block_list_params)
    # Create the longer to launch with the blocklist transform.
    launcher = TransformLauncher(transform_runtime_config=BlockListTransformConfiguration())
    # Launch the ray actor(s) to process the input
    launcher.launch()