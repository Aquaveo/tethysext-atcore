import logging


log = logging.getLogger(__name__)


class ResultsMixin(object):
    """
    Provides convenience methods for managing a results. Requires attributes mixin.
    """
    ATTR_LAST_RESULT = 'last_result'
    results = []

    def get_result(self, result_id):
        """
        Get result with the given id.

        Args:
            result_id(str or uuid): id of the result.

        Returns:
            ResourceWorkflowResult: the result or None if not found.
        """
        for result in self.results:
            if str(result.id) == str(result_id):
                return result
        log.warning('Result with id "{}" not found.'.format(result_id))
        return None

    def get_result_by_codename(self, codename):
        """
        Get a result by the given codename.
        Args:
            codename(str): codename of the result.

        Returns:
            ResourceWorkflowResult: the result or None if not found.
        """
        for result in self.results:
            if str(result.codename) == str(codename):
                return result
        log.warning('Result with codename "{}" not found.'.format(codename))
        return None

    def get_last_result(self):
        """
        Get the result which was last viewed by the user.

        Returns:
            ResourceWorkflowResult: the last result or None if not found.
        """
        try:
            last_result_id = self.get_attribute(self.ATTR_LAST_RESULT)
            if last_result_id is not None:
                # Load the previously viewed result?
                result = self.get_result(last_result_id)

                if result is None:
                    log.warning('Result with id "{}" not found.'.format(last_result_id))
                return result

            return self.results[0]
        except IndexError:
            log.warning('No results found.')
            return None

    def set_last_result(self, result=None):
        """
        Set the id of the last result viewed by the user.

        Args:
           result(ResourceWorkflowResult): The result to mark as being last viewed.

        """
        if result not in self.results:
            raise ValueError('Result {} does not belong to this object.'.format(result))
        self.set_attribute(self.ATTR_LAST_RESULT, str(result.id))

    def get_adjacent_results(self, result):
        """
        Get the adjacent results the given result.

        Args:
            result(ResourceWorkflowResult): A result belonging to this workflow.

        Returns:
            ResourceWorkflowResult, ResourceWorkflowResult: previous and next results, respectively.
        """
        if result not in self.results:
            raise ValueError('Result {} does not belong to this object.'.format(result))

        index = self.results.index(result)
        previous_index = index - 1
        next_index = index + 1
        previous_result = self.results[previous_index] if previous_index >= 0 else None
        next_result = self.results[next_index] if next_index < len(self.results) else None
        return previous_result, next_result
