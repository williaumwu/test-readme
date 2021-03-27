class Main(newSchedStack):

    def __init__(self,stackargs):

        newSchedStack.__init__(self,stackargs)

        self.parse.add_required(key="repo_branch",default="dev")
        self.parse.add_required(key="repo_key_group")
        self.parse.add_required(key="repo_url")

        self.parse.add_required(key="aws_default_region",default="us-east-1")
        self.parse.add_required(key="dockerfile",default="null")
        self.parse.add_required(key="docker_repo")
        self.parse.add_required(key="docker_tag_method",default="commit_hash")
        self.parse.add_required(key="config_env",default="private")
        self.parse.add_required(key="docker_host",default="null")

        # dockerfile_test
        self.parse.add_optional(key="dockerfile_test",default="null")

        # substacks can be referenced as fqn with <username>:::<repo>::<stack_name>
        # or <username>:::<stack_name> since stacks are first class citizens
        self.stack.add_substack("elasticdev:::ed_core::run_commit_info")
        self.stack.add_substack("elasticdev:::docker::ec2_standby_ci")
        self.stack.add_substack("elasticdev:::docker::docker_build")
        self.stack.add_substack("elasticdev:::ed_core::empty_stack")
        self.stack.add_substack('elasticdev:::ec2_server_stop')

        self.stack.init_substacks()

    def run_unit_test(self):

        self.parse.add_required(key="repo_url")
        self.init_variables()

        # Set docker host accordingly
        if not self.docker_host:
            self.docker_host = self.stackargs["docker_host"] = "{}-docker_host".format(self.stack.cluster)  

        # If not test scripts, we just return and skip unit_tests
        if not self.dockerfile_test:

            inputargs = {"default_values":{}}
            inputargs["automation_phase"] = "continuous_delivery"

            description = 'No (uni-)tests to run'
            inputargs["human_description"] = description
            inputargs["default_values"]["human_description"] = description

            inputargs["display_hash"] = self.stack.get_hash_object(inputargs)

            return self.stack.empty_stack.insert(display=True,**inputargs)
    
        # This sets the commit info need to register the image
        # we don't put this in the parsing arguments requested 
        # since it is retrieved from the "run"
        self.set_commit_info()
    
        default_values = {"commit_hash":self.commit_hash}
        default_values["config_env"] = self.config_env
        default_values["branch"] = self.repo_branch
        default_values["repo_branch"] = self.repo_branch
        default_values["repo_url"] = self.repo_url
        default_values["repo_key_group"] = self.repo_key_group
        if hasattr(self,"commit_info"): default_values["commit_info"] = self.commit_info
    
        # revisit 34098732086501259
        # currently, we placed the dockerfile right into
        # run variables.  in the future, we may want to 
        # separate this dockerfile (test) from dockerfile (build)
        # not urgent right now, in this instance, they run in order
        # from unit_test (dockerfile_test) to build (dockerfile)
        overide_values = {"docker_host":self.docker_host}
        overide_values["dockerfile"] = self.dockerfile_test
    
        inputargs = {"default_values":default_values,
                     "overide_values":overide_values}
    
        inputargs["automation_phase"] = "continuous_delivery"
        inputargs["human_description"] = 'Performing unit test with Dockerfile"{}"'.format(self.dockerfile_test)
    
        return self.stack.docker_build.insert(display=True,**inputargs)

    def run_record_commit(self):

        # init is set by the saas automatically 
        # when run for the first time
        self.parse.add_optional(key="init",default="null")
        self.parse.add_optional(key="commit_info",default="null")
        self.parse.add_optional(key="commit_hash",default="null")
        self.init_variables()

        if not self.commit_info and not self.init:
            msg = "you need commit_info unless this is the first code retrieval"
            self.stack.ehandle.NeedRtInput(message=msg)

        inputargs = {"automation_phase":"continuous_delivery"}
        inputargs["human_description"] = 'Publish commit_info'
        inputargs["default_values"] = {"commit_info":self.commit_info}
        return self.stack.run_commit_info.insert(display=True,**inputargs)

    def run_stop_server(self):

        self.init_variables()

        # Set docker host accordingly
        if not self.docker_host:
            self.docker_host = self.stackargs["docker_host"] = "{}-docker_host".format(self.stack.cluster)  

        default_values = {"hostname":self.docker_host}
        inputargs = {"default_values":default_values}
        inputargs["automation_phase"] = "continuous_delivery"
        inputargs["human_description"] = 'Stopping docker_host "{}"'.format(self.docker_host)

        return self.stack.ec2_server_stop.insert(display=True,**inputargs)

    def run_register_docker(self):

        self.parse.add_required(key="repo_url")
        self.init_variables()

        # Set docker host accordingly
        if not self.docker_host:
            self.docker_host = self.stackargs["docker_host"] = "{}-docker_host".format(self.stack.cluster)  

        # This sets the commit info need to register the image
        # we don't put this in the parsing arguments requested 
        # since it is retrieved from the "run"
        self.set_commit_info()

        default_values = {"docker_repo":self.docker_repo}
        default_values["repo_key_group"] = self.repo_key_group
        # We use the abbrev commit hash with 7 characters
        default_values["tag"] = self.commit_hash[0:6]
        default_values["config_env"] = self.config_env
        default_values["branch"] = self.repo_branch
        default_values["repo_branch"] = self.repo_branch
        default_values["repo_url"] = self.repo_url
        default_values["commit_hash"] = self.commit_hash
        default_values["docker_repo"] = self.docker_repo
        default_values["aws_default_region"] = self.aws_default_region
        if hasattr(self,"commit_info"): default_values["commit_info"] = self.commit_info

        # do we need to overide here?
        overide_values = {"docker_host":self.docker_host}
        overide_values["dockerfile"] = self.dockerfile

        inputargs = {"default_values":default_values,
                     "overide_values":overide_values}

        inputargs["automation_phase"] = "continuous_delivery"
        inputargs["human_description"] = 'Building docker container for commit_hash "{}"'.format(self.commit_hash)

        return self.stack.ec2_standby_ci.insert(display=True,**inputargs)

    def run(self):
    
        self.stack.unset_parallel()
        self.stack.add_job("unit_test",instance_name="auto")
        self.stack.add_job("record_commit",instance_name="auto")
        self.stack.add_job("register_docker",instance_name="auto")
        self.stack.add_job("stop_server",instance_name="auto")

        # Evaluating Jobs and loads
        for run_job in self.stack.get_jobs(): eval(run_job)

        return self.stack.get_results()

    def schedule(self):

        sched = self.stack.new_sched()
        sched.job = "record_commit"
        sched.archive.timeout = 600
        sched.archive.timewait = 120
        sched.archive.cleanup.instance = "clear"
        sched.failure.keep_resources = True
        sched.conditions.retries = 1
        sched.conditions.frequency = "wait_last_run 20"
        sched.conditions.noncurrent = [ "unit_test", "register_docker", "stop_server" ]
        sched.automation_phase = "continuous_delivery"
        sched.human_description = "Insert commit info into run"
        sched.on_success = [ "unit_test" ]
        self.stack.add_sched(sched)

        sched = self.stack.new_schedule()
        sched.job = "unit_test"
        sched.archive.timeout = 1800
        sched.archive.timewait = 180
        sched.archive.cleanup.instance = "clear"
        sched.failure.keep_resources = True
        sched.conditions.frequency = "wait_last_run 60"

        # Cannot have concurrency with a single docker host
        # The belows says another unit_test cannot run
        # while register_docker is running b/c they run on the 
        # same dockerhost.  This can change with a more sophisicated
        # stack.  This will also prevent a bunch of builds from completing
        # b/c of a race conditions.  It's not a big deal because 
        # the "runs" don't complete as it waits to stop the server, but
        # the unit_test and register of docker has completed.

        sched.conditions.noncurrent = [ "register_docker", "stop_server" ]
        sched.automation_phase = "continuous_delivery"
        sched.human_description = "Running unit_test for code"
        sched.on_success = [ "register_docker" ]
        sched.on_failure = [ "stop_server" ]
        self.stack.add_sched(sched)
        
        sched = self.stack.new_sched()
        sched.job = "register_docker"
        sched.archive.timeout = 1800
        sched.archive.timewait = 180
        sched.archive.cleanup.instance = "clear"
        sched.failure.keep_resources = True
        sched.conditions.noncurrent = [ "unit_test", "stop_server" ]
        sched.conditions.frequency = "wait_last_run 60"
        sched.automation_phase = "continuous_delivery"
        sched.human_description = "Building docker container with code"
        sched.on_success = [ "stop_server" ]
        sched.on_failure = [ "stop_server" ]
        self.stack.add_sched(sched)

        sched = self.stack.new_sched()
        sched.job = "stop_server"
        sched.archive.timeout = 300
        sched.archive.timewait = 10
        sched.archive.cleanup.instance = "clear"
        sched.failure.keep_resources = True
        sched.conditions.noncurrent = [ "unit_test", "register_docker" ]
        sched.conditions.frequency = "wait_last_run 10"
        sched.automation_phase = "continuous_delivery"
        sched.human_description = "Stopping docker host"
        self.stack.add_sched(sched)

        return self.stack.schedules
