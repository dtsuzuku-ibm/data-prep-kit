# execute Ray jobs
import sys
import os
from kfp_support.workflow_support.utils import KFPUtils, RayRemoteJobs


def execute_ray_jobs(
    name: str,  # name of Ray cluster
    additional_params: str,
    exec_params: str,
    exec_script_name: str,
    server_url: str,
) -> None:
    """
    Execute Ray job on a cluster periodically printing execution log
    :param name: cluster name
    :param additional_params: additional parameters for the job
    :param exec_params: job execution parameters
    :param exec_script_name: script to run (has to be present in the image)
    :param server_url: API server url
    :return: None
    """
    # add run id
    exec_params["job_id"] = os.getenv("ARGO_POD_UID"),
    # get current namespace
    ns = KFPUtils.get_namespace()
    if ns == "":
        print(f"Failed to get namespace")
        sys.exit(1)
    # Get parameters necessary for submitting
    additional_params_dict = KFPUtils.load_from_json(additional_params)
    exec_params = KFPUtils.load_from_json(exec_params)
    # Get credentials
    access_key, secret_key, cos_url = KFPUtils.credentials()
    exec_params["s3_cred"] = (
        "{'access_key': '" + access_key + "', 'secret_key': '" + secret_key + "', 'cos_url': '" + cos_url + "'}"
    )
    remote_jobs = RayRemoteJobs(
        server_url=server_url,
        http_retries=additional_params_dict.get("http_retries", 5),
        wait_interval=additional_params_dict.get("wait_interval", 2),
    )
    # submit job
    status, error, submission = remote_jobs.submit_job(
        name=name, namespace=ns, request=exec_params, executor=exec_script_name
    )
    print(f"submit job - status: {status}, error: {error}, submission id {submission}")
    # print execution log
    remote_jobs.follow_execution(
        name=name,
        namespace=ns,
        submission_id=submission,
        print_timeout=additional_params_dict.get("wait_print_tmout", 120),
        job_ready_timeout=additional_params_dict.get("wait_job_ready_tmout", 600),
    )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Execute Ray job operation")
    parser.add_argument("-rn", "--ray_name", type=str, default="")
    parser.add_argument("-id", "--run_id", type=str, default="")
    parser.add_argument("-ap", "--additional_params", type=str, default="{}")
    parser.add_argument("-n", "--notifier_str", type=str, default="")
    # The component converts the dictionary to json string
    parser.add_argument("-ep", "--exec_params", type=str, default="{}")
    parser.add_argument("-esn", "--exec_script_name", default="transformer_launcher.py", type=str)
    parser.add_argument("-su", "--server_url", type=str, default="")

    args = parser.parse_args()

    cluster_name = KFPUtils.runtime_name(
        ray_name=args.ray_name,
        run_id=args.run_id,
    )

    execute_ray_jobs(
        name=cluster_name,
        additional_params=args.additional_params,
        exec_params=args.exec_params,
        exec_script_name=args.exec_script_name,
        server_url=args.server_url,
    )
