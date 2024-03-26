import time
import traceback
from typing import Any

import pyarrow as pa
import ray
from data_processing.utils import get_logger, TransformUtils


logger = get_logger(__name__)


@ray.remote(scheduling_strategy="SPREAD")
class TransformTableProcessor:
    """
    This is the class implementing the actual work/actor processing of a single pyarrow file
    """

    def __init__(self, params: dict[str, Any]):
        """
        Init method
        :param params: dictionary that has the following key
            data_access_factory: data access factory
            transform_class: local transform class
            transform_params: dictionary of parameters for local transform creation
            statistics: object reference to statistics
            base_table_stats: boolean to peg base table stats
        """
        # Create data access
        self.data_access = params.get("data_access_factory", None).create_data_access()
        # Add data access ant statistics to the processor parameters
        transform_params = params.get("transform_params", None)
        transform_params["data_access"] = self.data_access
        # Create local processor
        self.transform = params.get("transform_class", None)(transform_params)
        # Create statistics
        self.stats = params.get("statistics", None)
        self.base_table_stats = params.get("base_table_stats", True)
        self.last_empty = " "

    def process_data(self, f_name: str) -> None:
        """
        Method processing an individual file
        :param f_name: file name
        :return: None
        """
        logger.debug(f"Begin processing file {f_name}")
        if self.data_access is None:
            logger.warning("No data_access found. Returning.")
        return
        t_start = time.time()
        # Read source table
        table = self.data_access.get_table(path=f_name)
        if table is None:
            logger.warning("File read resulted in None. Returning.")
            self.stats.add_stats.remote({"failed_reads": 1})
            return
        if self.base_table_stats:
            self.stats.add_stats.remote({"source_files": 1, "source_size": table.nbytes})
        # Process input table
        try:
            if table.num_rows > 0:
                # execute local processing
                logger.debug(f"Begin transforming table from {f_name}")
                out_tables, stats = self.transform.transform(table=table)
                logger.debug(f"Done transforming table from {f_name}")
            else:
                logger.info(f"table: {f_name} is empty, skipping processing")
                self.stats.add_stats.remote({"skipped empty tables": 1})
                return
            # save results
            self._submit_table(f_name=f_name, t_start=t_start, out_tables=out_tables, stats=stats)
        except Exception as e:
            logger.warning(f"Exception {e} processing file {f_name}: {traceback.format_exc()}")

    def flush(self) -> None:
        """
        This is supporting method for transformers, that implement buffering of tables, for example coalesce.
        These transformers can have buffers containing tables that were not written to the output. Flush is
        the hook for them to return back locally stored tables and their statistics.
        :return: None
        """
        t_start = time.time()
        try:
            # get flush results
            logger.debug(f"Begin flushing transform")
            out_tables, stats = self.transform.flush()
            logger.debug(f"Done flushing transform")
            # Here we are using the name of the last table, that did not return anything
            self._submit_table(f_name=self.last_empty, t_start=t_start, out_tables=out_tables, stats=stats)
        except Exception as e:
            logger.warning(f"Exception {e} flushing: {traceback.format_exc()}")

    def _submit_table(self, f_name: str, t_start: float, out_tables: list[pa.Table], stats: dict[str, Any]) -> None:
        """
        This is a helper method writing output tables and statistics
        :param f_name: input file n
        :param t_start: execution start time
        :param out_tables: list of tables to write
        :param stats: execution statistics to populate
        :return: None
        """
        # Compute output file location. Preserve sub folders for Wisdom
        match len(out_tables):
            case 0:
                # no tables - save input file name for flushing
                logger.debug(f"Transform did not produce a transformed table for file {f_name}")
                self.last_empty = f_name
            case 1:
                # we have exactly 1 table
                output_name = self.data_access.get_output_location(path=f_name)
                logger.debug(f"Writing transformed file {f_name} to {output_name}")
                if TransformUtils.verify_no_duplicate_columns(table=out_tables[0], file=output_name):
                    output_file_size, save_res = self.data_access.save_table(path=output_name, table=out_tables[0])
                    if save_res is not None:
                        # Store execution statistics. Doing this async
                        if self.base_table_stats:
                            self.stats.add_stats.remote(
                                {
                                    "result_files": 1,
                                    "result_size": out_tables[0].nbytes,
                                    "table_processing": time.time() - t_start,
                                }
                            )
                    else:
                        logger.warning(f"Failed to write file {output_name}")
                        self.stats.add_stats.remote({"failed_writes": 1})
            case _:
                # we have more then 1 table
                table_sizes = 0
                output_name = self.data_access.get_output_location(path=f_name)
                output_file_name = output_name.removesuffix(".parquet")
                count = len(out_tables)
                for index in range(count):
                    if TransformUtils.verify_no_duplicate_columns(table=out_tables[index], file=output_name):
                        output_name_indexed = f"{output_file_name}_{index}.parquet"
                        table_sizes += out_tables[index].nbytes
                        logger.debug(f"Writing transformed file {f_name}, {index + 1} of {count}  to {output_name_indexed}")
                        output_file_size, save_res = self.data_access.save_table(
                            path=output_name_indexed, table=out_tables[index]
                        )
                        if save_res is None:
                            logger.warning(f"Failed to write file {output_name_indexed}")
                            self.stats.add_stats.remote({"failed_writes": 1})
                            break
                if self.base_table_stats:
                    self.stats.add_stats.remote(
                        {
                            "result_files": len(out_tables),
                            "result_size": table_sizes,
                            "table_processing": time.time() - t_start,
                        }
                    )
        # save transformer's statistics
        if len(stats) > 0:
            self.stats.add_stats.remote(stats)
