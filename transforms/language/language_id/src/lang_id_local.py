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

from data_processing.data_access import DataAccessLocal
from data_processing.utils import DPLConfig, ParamsUtils
from lang_id_transform import (
    PARAM_CONTENT_COLUMN_NAME,
    PARAM_MODEL_CREDENTIAL,
    PARAM_MODEL_KIND,
    PARAM_MODEL_URL,
    LangIdentificationTransform,
)
from lang_models import KIND_FASTTEXT


# create parameters
input_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), "../test-data/input"))

langid_config = {
    PARAM_MODEL_KIND: KIND_FASTTEXT,
    PARAM_MODEL_URL: "facebook/fasttext-language-identification",
    PARAM_MODEL_CREDENTIAL: DPLConfig.HUGGING_FACE_TOKEN,
    PARAM_CONTENT_COLUMN_NAME: "text",
}

if __name__ == "__main__":
    # Here we show how to run outside of ray
    # Create and configure the transform.
    transform = LangIdentificationTransform(langid_config)
    # Use the local data access to read a parquet table.
    data_access = DataAccessLocal()
    table = data_access.get_table(os.path.join(input_folder, "test_01.parquet"))
    print(f"input table: {table}")
    # Transform the table
    table_list, metadata = transform.transform(table)
    table = table_list[0]
    print(f"\noutput table: {table}")
    print(f"output metadata : {metadata}")
    print(f"language column : {table['ft_lang']}")
    print(f"score column : {table['ft_score']}")