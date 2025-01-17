# (C) Copyright IBM Corp. 2024.
# Licensed under the Apache License, Version 2.0 (the “License”);
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#  http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an “AS IS” BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
################################################################################

import os
import sys
import ast

from data_processing_ray.runtime.ray import RayTransformLauncher
from data_processing.utils import ParamsUtils, GB
from ingest_2_parquet_transform_ray import (
    IngestToParquetRayConfiguration,
    ingest_supported_langs_file_key,
    ingest_detect_programming_lang_key,
    ingest_domain_key,
    ingest_snapshot_key,
)


# create parameters
supported_languages_file = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../test-data/languages/lang_extensions.json")
)
input_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), "../test-data/input"))
output_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), "../output"))
local_conf = {
    "input_folder": input_folder,
    "output_folder": output_folder,
}
worker_options = {"num_cpus": 0.8, "memory": 2*GB}
code_location = {"github": "github", "commit_hash": "12345", "path": "path"}
ingest_config = {
    ingest_supported_langs_file_key: supported_languages_file,
    ingest_detect_programming_lang_key: True,
    ingest_snapshot_key: "github",
    ingest_domain_key: "code",
}

params = {
    # where to run
    "run_locally": True,
    # Data access. Only required parameters are specified
    "data_local_config": ParamsUtils.convert_to_ast(local_conf),
    "data_files_to_use": ast.literal_eval("['.zip']"),
    # orchestrator
    "runtime_worker_options": ParamsUtils.convert_to_ast(worker_options),
    "runtime_num_workers": 3,
    "runtime_pipeline_id": "pipeline_id",
    "runtime_job_id": "job_id",
    "runtime_creation_delay": 0,
    "runtime_code_location": ParamsUtils.convert_to_ast(code_location),
}

if __name__ == "__main__":
    sys.argv = ParamsUtils.dict_to_req(d=(params | ingest_config))
    # create launcher
    launcher = RayTransformLauncher(IngestToParquetRayConfiguration())
    # launch
    launcher.launch()
