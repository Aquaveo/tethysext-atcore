"""
********************************************************************************
* Name: condor_workflow_manager.py
* Author: nswain
* Created On: March 13, 2019
* Copyright: (c) Aquaveo 2019
********************************************************************************
"""
import os
from tethys_sdk.jobs import CondorWorkflowJobNode
from tethys_sdk.compute import get_scheduler
from .base_workflow_manager import BaseWorkflowManager


class ResourceWorkflowCondorJobManager(BaseWorkflowManager):
    """
    Helper class that prepares and submits condor workflows/jobs for resource workflows.
    """

    def prepare(self):
        """
        Prepares all workflow jobs for processing upload to database.

        Returns:
            int: the job id.
        """
        # Prep
        scheduler = get_scheduler(self.scheduler_name)
        # TODO: Cleanup other jobs associated with this workflow...
        job_manager = self.app.get_job_manager()

        # Create Workflow
        self.workflow = job_manager.create_job(
            name=self.safe_job_name,
            description='{}: {}'.format(self.resource_workflow_type, self.resource_workflow_step_name),
            job_type='CONDORWORKFLOW',
            workspace=self.workspace,
            user=self.user,
            scheduler=scheduler,
            extended_properties={
                'resource_id': self.resource_id,
                'resource_workflow_id': self.resource_workflow_id,
                'resource_workflow_step_id': self.resource_workflow_step_id,
            }
        )

        # Save the workflow
        self.workflow.save()

        # Preprocess jobs if they are dicts
        if self.jobs_are_dicts:
            self.jobs = self._build_job_nodes(self.jobs)

        # Add file names as args
        input_file_names = []
        for input_file in self.input_files:
            input_file_name = os.path.split(input_file)[1]
            input_file_names.append(input_file_name)
            self.job_args.append(input_file_name)

        # Parametrize each job
        for job in self.jobs:
            # Set arguments for each job
            job.set_attribute('arguments', self.job_args)

            # Add input files to transfer input files
            transfer_input_files_str = job.get_attribute('transfer_input_files') or ''
            transfer_input_files = transfer_input_files_str.split(',')

            for input_file_name in input_file_names:
                transfer_input_files.append('../{}'.format(input_file_name))

            job.set_attribute('transfer_input_files', transfer_input_files)

            # Add additional remote input file
            remote_input_files = job.remote_input_files
            remote_input_files.extend(self.input_files)
            job.remote_input_files = remote_input_files

            # Save the job
            job.save()

        # Create update status job
        update_status_job = CondorWorkflowJobNode(
            name='finalize',  # Better for display name
            condorpy_template_name='vanilla_transfer_files',
            remote_input_files=[
                os.path.join(self.ATCORE_EXECUTABLE_DIR, 'update_status.py'),
            ],
            workflow=self.workflow
        )

        update_status_job.set_attribute('executable', 'update_status.py')
        update_status_job.set_attribute('arguments', self.job_args)

        update_status_job.save()

        # Bind update_status job only to terminal nodes in the workflow (jobs without children)
        for job in self.jobs:
            if len(job.children_nodes.select_subclasses()) <= 0:
                update_status_job.add_parent(job)

        self.jobs.append(update_status_job)

        update_status_job.save()

        # Save Condor Workflow Job
        self.prepared = True

        return self.workflow.id

    def _build_job_nodes(self, job_dicts):
        """
        Build CondorWorkflowJobNodes from the job_dicts provided.

        Args:
            job_dicts(list<dicts>): A list of dictionaries, each containing the kwargs for a CondorWorkflowJobNode.

        Returns:
            list<CondorWorkflowJobNodes>: the job nodes.
        """
        from tethys_sdk.jobs import CondorWorkflowJobNode

        jobs = []
        job_map = {}

        # Create all the jobs
        for job_dict in job_dicts:
            # Pop-off keys to be handled separately
            parents = job_dict.pop('parents', [])
            attributes = job_dict.pop('attributes', {})

            job_dict.update({'workflow': self.workflow})

            job = CondorWorkflowJobNode(**job_dict)

            for attribute, value in attributes.items():
                job.set_attribute(attribute, value)

            job.save()
            jobs.append(job)

            # For mapping relationships
            job_map[job.name] = {'job': job, 'parents': parents}

        # Set Parent Relationships
        for job in jobs:
            for parent_name in job_map[job.name]['parents']:
                job.add_parent(job_map[parent_name]['job'])

            job.save()

        return jobs
