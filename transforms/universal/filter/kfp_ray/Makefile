REPOROOT=${CURDIR}/../../../../
WORKFLOW_VENV_ACTIVATE=${REPOROOT}/transforms/venv/bin/activate
include $(REPOROOT)/transforms/.make.workflows

SRC_DIR=${CURDIR}/../ray/

PYTHON_WF := $(shell find ./ -name '*_wf.py')
YAML_WF := $(patsubst %.py, %.yaml, ${PYTHON_WF})

workflow-venv: .check_python_version ${WORKFLOW_VENV_ACTIVATE}

clean:: .defaults.clean

setup:: 

venv::

build::

test::

test-src::

test-image::

publish::

image::

load-image::

set-versions: workflow-reconcile-requirements

.PHONY: workflow-build
workflow-build: workflow-venv
	$(MAKE) $(YAML_WF)

.PHONY: workflow-test
workflow-test: workflow-build
	$(MAKE) .transforms_workflows.test-pipeline TRANSFORM_SRC=${SRC_DIR} PIPELINE_FILE=filter_wf.yaml

.PHONY: workflow-upload
workflow-upload: workflow-build
	@for file in $(YAML_WF); do \
		$(MAKE) .transforms_workflows.upload-pipeline PIPELINE_FILE=$$file; \
	done

.PHONY: workflow-reconcile-requirements
workflow-reconcile-requirements:
	@for file in $(PYTHON_WF); do \
		$(MAKE) .transforms_workflows.reconcile-requirements PIPELINE_FILE=$$file; \
	done
