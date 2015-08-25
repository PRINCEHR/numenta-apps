#!/usr/bin/env python
# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2015, Numenta, Inc.  Unless you have purchased from
# Numenta, Inc. a separate commercial license for this software code, the
# following terms and conditions apply:
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero Public License version 3 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU Affero Public License for more details.
#
# You should have received a copy of the GNU Affero Public License
# along with this program.  If not, see http://www.gnu.org/licenses.
#
# http://numenta.org/licenses/
# ----------------------------------------------------------------------

import argparse
import json
import os

from grok.pipeline.utils import build_commands as builder
from grok.pipeline.utils import getGithubUserName
from grok.pipeline.utils.helpers import checkIfSaneProductionParams
from infrastructure.utilities import git
from infrastructure.utilities import diagnostics
from infrastructure.utilities.env import prepareEnv
from infrastructure.utilities.path import changeToWorkingDir


def getDeployTrack(grokRemote, grokBranch):
  """
    This method gives us the deployTrack, depending upon parameters
    (basically checks if production parameters or not).

    :param grokRemote: URL for Grok remote repository
    :param grokBranch:  Grok branch used for current build

    :returns: A `string` representing the deployment track
    e.g.
    1)
    grokRemote: git@github.com:<user-name>/numenta-apps.git
    deployTrack: <user-name>-numenta
    2)
    grokRemote: git@github.com:Numenta/numenta-apps.git
    deployTrack: groksolutions

    :rtype: string
  """
  if checkIfSaneProductionParams(grokRemote, grokBranch):
    return "groksolutions"
  else:
    return getGithubUserName(grokRemote) + "-numenta"


def preBuildSetup(env, pipelineConfig):
  """
    Clone the Grok repo if needed and get it set to the right remote, branch,
    and SHA.

    :param env: The environment variable which is set before building
    :param pipelineConfig: dict of the pipeline config values, e.g.:
      {
        "buildWorkspace": "/path/to/build/in",
        "grokRemote": "git@github.com:Numenta/numenta-apps.git",
        "grokBranch": "master",
        "grokSha": "HEAD",
        "pipelineParams": "{dict of parameters}",
        "pipelineJson": "/path/to/json/file"
      }

    :returns: The updated pipelineConfig dict
    :rtype: dict
  """
  diagnostics.printEnv(env, g_logger)

  # Clone Grok if needed, otherwise, setup remote
  with changeToWorkingDir(pipelineConfig["buildWorkspace"]):
    if not os.path.isdir(env["GROK_HOME"]):
      git.clone(gitURL=pipelineConfig["grokRemote"],
                directory="products",
                logger=g_logger)

  with changeToWorkingDir(env["GROK_HOME"]):
    if pipelineConfig["grokSha"]:
      g_logger.debug("Resetting to %s", pipelineConfig["grokSha"])
      git.resetHard(sha=pipelineConfig["grokSha"], logger=g_logger)
    else:
      grokSha = git.getShaFromRemoteBranch(pipelineConfig["grokRemote"],
                                           pipelineConfig["grokBranch"],
                                           logger=g_logger)
      pipelineConfig["grokSha"] = grokSha
      g_logger.debug("Resetting to %s", grokSha)
      git.resetHard(sha=grokSha, logger=g_logger)


def addAndParseArgs(jsonArgs):
  """
    Parse the command line arguments or a json blog containing the required
    values.

    :returns: A dict of the parameters needed, as follows:
      {
        "buildWorkspace": "/path/to/build/in",
        "grokRemote": "git@github.com:Numenta/numenta-apps.git",
        "grokBranch": "master",
        "grokSha": "HEAD",
        "pipelineParams": "{dict of parameters}",
        "pipelineJson": "/path/to/json/file"
      }

    :rtype: dict

    :raises parser.error in case wrong combination of arguments or arguments
      are missing.
  """
  parser = argparse.ArgumentParser(description="build tool for Grok")
  parser.add_argument("--pipeline-json", dest="pipelineJson", type=str,
                      help="The JSON file generated by manifest tool.")
  parser.add_argument("--build-workspace", dest="buildWorkspace", type=str,
                      help="Common dir prefix for Grok")
  parser.add_argument("--grok-remote", dest="grokRemote", type=str,
                      help="The grok remote you want to use, e.g.,  "
                           "git@github.com:Numenta/numenta-apps.git")
  parser.add_argument("--grok-sha", dest="grokSha", type=str,
                      help="Grok SHA that will be built")
  parser.add_argument("--grok-branch", dest="grokBranch", type=str,
                      help="The branch you are building from")
  parser.add_argument("--release-version", dest="releaseVersion", type=str,
                      help="Current release version, this will be used as base"
                           "version for grok and tracking rpm")
  parser.add_argument("--log", dest="logLevel", type=str, default="warning",
                      help="Logging level, by default it takes warning")

  args = {}
  if jsonArgs:
    args = jsonArgs
  else:
    args = vars(parser.parse_args())

  global g_logger
  g_logger = diagnostics.initPipelineLogger("build", logLevel=args["logLevel"])
  saneParams = {k:v for k, v in args.items() if v is not None}
  del saneParams["logLevel"]

  if "pipelineJson" in saneParams and len(saneParams) > 1:
    errorMessage = "Please provide parameters via JSON file or commandline"
    parser.error(errorMessage)

  if "pipelineJson" in saneParams:
    with open(args["pipelineJson"]) as paramFile:
      pipelineParams = json.load(paramFile)
  else:
    pipelineParams = saneParams

  # Setup defaults
  pipelineConfig = {
    "buildWorkspace": None,
    "grokRemote": "git@github.com:Numenta/numenta-apps.git",
    "grokBranch": "master",
    "grokSha": "HEAD",
    "pipelineParams": pipelineParams,
    "pipelineJson": None
  }

  pipelineConfig["buildWorkspace"] = os.environ.get("BUILD_WORKSPACE",
                    pipelineParams.get("buildWorkspace",
                      pipelineParams.get("manifest", {}).get("buildWorkspace")))
  if not pipelineConfig["buildWorkspace"]:
    parser.error("You must set a BUILD_WORKSPACE environment variable "
                 "or pass the --build-workspace argument via the command line "
                 "or json file.")

  pipelineConfig["grokRemote"] = pipelineParams.get("grokRemote",
                          pipelineParams.get("manifest", {}).get("grokRemote"))
  pipelineConfig["grokBranch"] = pipelineParams.get("grokBranch",
                          pipelineParams.get("manifest", {}).get("grokBranch"))
  pipelineConfig["grokSha"] = pipelineParams.get("grokSha",
                          pipelineParams.get("manifest", {}).get("grokSha"))

  pipelineConfig["pipelineJson"] = args["pipelineJson"]

  return pipelineConfig



def main(jsonArgs):
  """
    Main function.

    :param jsonArgs: dict of pipeline-json and logLevel, defaults to empty
      dict to make the script work independently and via driver scripts.
      e.g. {"pipelineJson" : <PIPELINE_JSON_PATH>,
            "logLevel" : <LOG_LEVEL>}

    :param jsonArgs: dict of  pipeline-json and logLevel
      e.g. {"pipelineJson" : <PIPELINE_JSON_PATH>,
            "logLevel" : <LOG_LEVEL>}
  """
  try:
    pipelineConfig = addAndParseArgs(jsonArgs)

    grokUser = getGithubUserName(pipelineConfig["grokRemote"])
    amiName = (grokUser + "-" + pipelineConfig["grokBranch"])
    env = prepareEnv(pipelineConfig["buildWorkspace"], None, os.environ)

    preBuildSetup(env, pipelineConfig)

    builder.buildGrok(env, pipelineConfig, g_logger)
    g_logger.debug("Grok built successfully!")

    deployTrack = getDeployTrack(pipelineConfig["grokRemote"],
                                 pipelineConfig["grokBranch"])

    pipelineConfig["pipelineParams"]["build"] = {
                              "grokSha": pipelineConfig["grokSha"],
                              "grokHome": env["GROK_HOME"],
                              "deployTrack": deployTrack,
                              "grokDeployTrack": grokUser,
                              "amiName": amiName
                            }
    g_logger.debug(pipelineConfig["pipelineParams"])
    if pipelineConfig["pipelineJson"]:
      with open(pipelineConfig["pipelineJson"], 'w') as jsonFile:
        jsonFile.write(json.dumps(pipelineConfig["pipelineParams"],
                       ensure_ascii=False))
  except Exception:
    g_logger.exception("Unknown error occurred in build phase")
    raise



if __name__ == "__main__":
  main({})
