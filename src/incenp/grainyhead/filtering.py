# grainyhead - Helper tools for GitHub
# Copyright © 2021,2022,2025 Damien Goutte-Gattat
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

from datetime import datetime
from typing import Any

from .providers import RepositoryItem


class ItemFilter(object):
    """Base class for repository item filters."""

    @property
    def name(self) -> str:
        """The user-friendly name of the filter."""

        return str(self)

    def filter(self, _: Any) -> bool:
        """Tests the specified repository item.

        This method should be overriden by derived classes and
        return True if the item should be kept, or False if it
        should be filtered out.
        """

        return False


class NullFilter(ItemFilter):
    """A null filter that accepts all items."""

    def filter(self, _: Any) -> bool:
        return True

    def __str__(self) -> str:
        return "all"


class DateRangeFilter(ItemFilter):
    """A filter that accepts items based on their creation date.

    This filter will accept items that have been created during
    a given period.
    """

    def __init__(self, start: datetime, end: datetime):
        """Creates a new instance.

        :param start: beginning of the time period (items created
            before that time will be filtered out)
        :param end: end of the time period (items created after
            that time will be filtered out)
        """

        self._start = start
        self._end = end

    def __str__(self) -> str:
        return f"date:{self._start:%Y-%m-%d}..{self._end:%Y-%m-%d}"

    def filter(self, item: RepositoryItem) -> bool:
        return item.created(after=self._start, before=self._end)


class TeamFilter(ItemFilter):
    """A filter that accepts items originating from a given team.

    This filter will accept items that have been created by the
    members of a given team.
    """

    def __init__(self, team_name: str, members: list[str]):
        """Creates a new instance.

        :param team_name: the name of the team (for display purposes)
        :param members: list of team members' name
        """

        self._slug = team_name
        self._members = members

    def __str__(self) -> str:
        return f"team:{self._slug}"

    @property
    def name(self) -> str:
        return self._slug

    def filter(self, item: RepositoryItem) -> bool:
        return item.user_name in self._members


class UserFilter(ItemFilter):
    """A filter that accepts items originating from a given user."""

    def __init__(self, user_name: str):
        self._user = user_name

    def __str__(self) -> str:
        return f"user:{self._user}"

    @property
    def name(self) -> str:
        return f"@{self._user}"

    def filter(self, item: RepositoryItem) -> bool:
        return self._user == item.user_name


class LabelFilter(ItemFilter):
    """A filter that accepts items carrying a given label."""

    def __init__(self, label: str):
        self._label = label

    def __str__(self) -> str:
        return f"label:{self._label}"

    @property
    def name(self) -> str:
        return self._label

    def filter(self, item: RepositoryItem) -> bool:
        return self._label in item.label_strings


class ComplementFilter(ItemFilter):
    """A filter that inverts another filter.

    Given another filter, this filter will select the complement set
    of items. It will accept items that are rejected by the inner
    filter, and vice versa.
    """

    def __init__(self, inner_filter: ItemFilter):
        self._filter = inner_filter

    def __str__(self) -> str:
        return f"!{str(self._filter)}"

    @property
    def name(self) -> str:
        return f"!{self._filter.name}"

    def filter(self, item: RepositoryItem) -> bool:
        return not self._filter.filter(item)


class CombinedFilter(ItemFilter):
    """Base class for filters that are combinations of other filters."""

    def __init__(self, filters: list[ItemFilter], operator: str):
        """Creates a new instance.

        :param filters: the filters to combine
        :param operator: the operator to combine them
        """

        self._filters = filters
        self._op = operator

    def __str__(self) -> str:
        return f" {self._op} ".join([str(f) for f in self._filters])

    @property
    def name(self) -> str:
        return f" {self._op} ".join([f.name for f in self._filters])


class IntersectionFilter(CombinedFilter):
    """A filter that represents the intersection of a set of filters.

    This filter will accept items that are accepted by all the filters
    in the set.
    """

    def __init__(self, filters: list[ItemFilter]):
        CombinedFilter.__init__(self, filters, "&")

    def filter(self, item: RepositoryItem) -> bool:
        return False not in [f.filter(item) for f in self._filters]


class UnionFilter(CombinedFilter):
    """A filter that represents the union of a set of filters.

    This filter will accept items that are accepted by any of the
    filters in the set.
    """

    def __init__(self, filters: list[ItemFilter]):
        CombinedFilter.__init__(self, filters, "|")

    def filter(self, item: RepositoryItem) -> bool:
        return True in [f.filter(item) for f in self._filters]


class DifferenceFilter(CombinedFilter):
    """A filter that represents the difference of a set of two filters.

    This filter will accept items that are accepted by one of the
    filters in the set and rejected by the other filter.
    """

    def __init__(self, filters: list[ItemFilter]):
        CombinedFilter.__init__(self, filters, "^")

    def filter(self, item: RepositoryItem) -> bool:
        return len([r for r in [f.filter(item) for f in self._filters] if r]) == 1
