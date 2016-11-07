import json
import requests

from requests.exceptions import ConnectionError
from six.moves.urllib.parse import urljoin

from flask import current_app
from .utils import get_job_level, get_job_human_status, transform_arguments

from .core import ExpiredToken, Unauthorized, InvalidURI, JobNotStarted, HTTPSaltStackSession

class HTTPSaltStackClient_2(object):

    def __init__(self, master, api_url, salt_user, salt_password, verify_ssl=True, eauth = 'pam'):
        self.session = HTTPSaltStackSession()
        self.master = master
        self.api_url = api_url
        self.salt_user = salt_user
        self.salt_password = salt_password
        self.verify_ssl = verify_ssl
        self.eauth = eauth

    def urljoin(self, *parts):
        return urljoin(self.api_url, '/'.join(parts))

    def login(self):
        headers = {'accept': 'application/json'}
        data = {'username': self.salt_user, 'password': self.salt_password, 'eauth': self.eauth}
        return self.session.post(self.urljoin('login'), data=data,
            headers=headers, verify=self.verify_ssl)['return'][0]

    def minions(self):
        token = self.get_token()
        headers = {'accept': 'application/json', 'X-Auth-Token': token}
        r = self.session.get(self.urljoin('minions'), headers=headers, verify=self.verify_ssl)
        return r['return'][0]

    def minion_details(self, minion):
        token = self.get_token()
        headers = {'accept': 'application/json', 'X-Auth-Token': token}
        return self.session.get(self.urljoin('minions', minion), headers=headers, verify=self.verify_ssl)

    def minions_status(self):
        return self.run("manage.status", client="runner")

    def jobs(self, minion=None):
        token = self.get_token()
        headers = {'accept': 'application/json', 'X-Auth-Token': token}
        r = self.session.get(self.urljoin('jobs'), headers=headers, verify=self.verify_ssl)

        return r['return'][0]

    def job(self, jid, minion=None):
        token = self.get_token()
        headers = {'accept': 'application/json', 'X-Auth-Token': token}
        r = self.session.get(self.urljoin('jobs', jid), headers=headers, verify=self.verify_ssl)

        if not r['return'][0]:
            output = {'status': 'running', 'info': r['info'][0]}
            return output

        # Only filter minion
        if minion:
            minion_return = r['return'][0]['data'][minion]
            output = {'return': minion_return, 'info': r['info']}

            return output

        return {'info': r['info'][0], 'return': r['return'][0]}

    def jobs_batch(self, jobs):
        token = self.get_token()

        data = [{"fun": "jobs.lookup_jid", "jid": jid, "client": 'runner'}
            for jid in jobs]

        headers = {'accept': 'application/json', 'X-Auth-Token': token,
            'content-type': 'application/json'}
        r = self.session.post(self.endpoint, data=json.dumps(data),
            headers=headers, verify=self.verify_ssl)
        if not r['return']:
            return {}

        for jid, job_return in zip(jobs, r['return']):
            if job_return.get('data'):
                jobs[jid]['return'] = job_return['data']
            else:
                jobs[jid]['return'] = job_return
        return jobs


    def select_jobs(self, fun, minions=None, with_details=False, **arguments):
        jobs = {}

        default_arguments_values = arguments.pop('default_arguments_values', {})

        jids = {}

        # Pre-match
        for jid, job in self.jobs().items():
            if job['Function'] != fun:
                continue

            _, job_args_kwargs = transform_arguments(job['Arguments'])

            match = True
            for argument, argument_value in list(arguments.items()):

                default_argument_value = default_arguments_values.get(argument)

                if job_args_kwargs.get(argument, default_argument_value) != argument_value:
                    match = False
                    break

            if not match:
                continue

            jids[jid] = job

            if not (minions or with_details):
                jobs.setdefault('*', {})[jid] = job


        # Get each job detail if needed
        if minions or with_details:
            job_returns = self.jobs_batch(jids)

            for jid, job_details in job_returns.items():

                # Running job
                if job_details.get('status') == 'running':
                    for minion_name in job_details['info']['Minions']:
                        minion_data = job_details
                        jobs.setdefault(minion_name, {})[jid] = minion_data
                    continue

                job_return = job_details['return']

                for minion_name, minion_return in job_return.items():
                    if not minion_name in minions:
                        continue

                    # Error has been detected
                    if isinstance(minion_return, list):

                        minion_data = {'return': minion_return,
                            'status': 'error', 'info': job}
                        jobs.setdefault(minion_name, {})[jid] = minion_data
                        continue

                    minion_data = {'return': minion_return, 'info': job}

                    if with_details and isinstance(minion_return, dict):
                        minion_data['level'] = get_job_level(minion_return)
                        minion_data['status'] = get_job_human_status(minion_data['level'])
                    else:
                        minion_data['level'] = False
                        minion_data['status'] = 'error'

                    jobs.setdefault(minion_name, {})[jid] = minion_data


        return jobs

    def run(self, fun, tgt=None, expr_form=None, client=None, args=[], **kwargs):
        token = self.get_token()
        data = [{
            "fun": fun,
            "arg": args,
        }]

        if tgt:
            data[0]['tgt'] = tgt

        if expr_form:
            data[0]['expr_form'] = expr_form

        if client:
            data[0]['client'] = client

        data[0].update(kwargs)

        headers = {'accept': 'application/json', 'X-Auth-Token': token,
            'content-type': 'application/json'}
        r = self.session.post(self.endpoint, data=json.dumps(data),
            headers=headers, verify=self.verify_ssl)
        if not r['return'][0]:
            raise JobNotStarted("Couldn't run job")
        return r['return'][0]
