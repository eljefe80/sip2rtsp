
from pathlib import Path
from subprocess import call

SERVICE_DIR="/var/services"

RUN_CONTENTS="""#!/command/with-contenv bash
# shellcheck shell=bash
# Start the {execb} service

set -o errexit -o nounset -o pipefail

# Tell S6-Overlay not to restart this service
s6-svc -O .

echo "[INFO] Starting {execb}..." >&2

# Replace the bash process with the {execb} process, redirecting stderr to stdout
exec 2>&1
exec {execb} -f {dir} -v
"""

FINISH_CONTENTS="""#!/command/with-contenv bash
# shellcheck shell=bash
# Take down the S6 supervision tree when the service exits

set -o errexit -o nounset -o pipefail

declare exit_code_container
exit_code_container=$(cat /run/s6-linux-init-container-results/exitcode)
readonly exit_code_container
readonly exit_code_service="${{1}}"
readonly exit_code_signal="${{2}}"
readonly service="{execb}"

echo "Service ${{service}} exited with code ${{exit_code_service}} (by signal ${{exit_code_signal}})" >&2

if [[ "${{exit_code_service}}" -eq 256 ]]; then
  if [[ "${{exit_code_container}}" -eq 0 ]]; then
    echo $((128 + exit_code_signal)) > /run/s6-linux-init-container-results/exitcode
  fi
elif [[ "${{exit_code_service}}" -ne 0 ]]; then
  if [[ "${{exit_code_container}}" -eq 0 ]]; then
    echo "${{exit_code_service}}" > /run/s6-linux-init-container-results/exitcode
  fi
  exec /run/s6/{execb}/bin/halt
fi
"""

class S6Generator():

    def __init__(self, name, execb, config, type="longrun", timeout=30000, producerfor=None, dependencies=None, dir=None):
        self.name = name
        self.execb = execb
        self.type = type
        self.config = config
        self.dir = (dir or SERVICE_DIR)+f"/{execb}-{name}"
        self.timeout = timeout
        self.producerfor = producerfor
        self.dependencies = dependencies

    def generate_files(self):
        Path(self.dir).mkdir(parents=True, exist_ok=True)
        with open(self.dir+"/run", "w+") as file:
            file.write(
                RUN_CONTENTS.format(
                    execb=self.execb,
                    dir=Path(self.config).parents[0]
                )
            )
        Path(self.dir+"/run").chmod(0o700)
        print(self.dir+"/run", Path(self.dir+"/run").stat().st_mode)
        with open(self.dir+"/finish", "w+") as file:
            file.write(
                FINISH_CONTENTS.format(
                    execb=self.execb
                )
            )
        Path(self.dir+"/finish").chmod(0o700)
        with open(self.dir+"/timeout-kill", "w+") as file:
            file.write(str(self.timeout))
        with open(self.dir+"/type", "w+") as file:
            file.write(self.type)
        with open(self.dir+"/producer-for", "w+") as file:
            file.write(self.producerfor) if self.producerfor is not None else ""
        for dependency in (self.dependencies or []):
            open(self.dir+"/dependencies.d/"+dependency, "x")

    def start_supervisor(self):
        ret = call(f"find / | grep s6-svlink", shell=True)
        print(ret)
        ret = call(f"s6-svlink /run/service {self.dir}", shell=True)
