# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You may not use this file except in compliance
# with the License. A copy of the License is located at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# or in the "license" file accompanying this file. This file is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES
# OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing
# permissions and limitations under the License.

# Pydantic models of the Landing Zone Accelerator on AWS configuration schema
# (https://github.com/awslabs/landing-zone-accelerator-on-aws, Apache-2.0). The field descriptions
# are LZA's own documentation. Generated, and replaced as a unit when the pack moves to a new LZA
# release; edits made here by hand are lost at that point.
from __future__ import annotations

from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

type NonEmptyString = Annotated[
    str,
    Field(
        description="## Non-Empty String Type\n\nRepresents a string that must contain at least one character. Used for required text fields throughout the Landing Zone Accelerator configuration where empty values are not permitted.\n\n```",
        min_length=1,
    ),
]


class ParameterReplacementType(StrEnum):
    ssm = "SSM"
    string = "String"
    string_list = "StringList"
    number = "Number"


class ParameterReplacement(BaseModel):
    model_config = ConfigDict(extra="forbid")
    key: Annotated[str, Field(description="Key of the replacement placeholder", min_length=1)]
    path: Annotated[str, Field(description="Path of the SSM Parameter containing the value to replace", min_length=1)]


class ParameterReplacementV2(BaseModel):
    model_config = ConfigDict(extra="forbid")
    key: Annotated[str, Field(description="Key of the replacement placeholder", min_length=1)]
    path: Annotated[str | None, Field(description="Path of the SSM Parameter containing the value to replace", min_length=1)] = None
    type: Annotated[ParameterReplacementType, Field(description="Type of the global parameters")]
    value: Annotated[NonEmptyString | list[NonEmptyString] | float | None, Field(description="Value of the parameter if type is string or array")] = (
        None
    )


class ReplacementsConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    global_replacements: Annotated[
        list[ParameterReplacement | ParameterReplacementV2] | None,
        Field(
            alias="globalReplacements",
            description="The set of placeholder parameters (key/path pairs) that will be merged with yaml configuration files.",
        ),
    ] = None


type Model = ReplacementsConfig
