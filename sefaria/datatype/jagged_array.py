"""
jagged_array.py: a sparse array of arrays

http://stackoverflow.com/questions/8180014/how-to-subclass-python-list-without-type-problems
https://docs.python.org/2/reference/datamodel.html
Mutable sequences should provide methods
append(), count(), index(), extend(), insert(), pop(), remove(), reverse() and sort(),
like Python standard list objects.
Finally, sequence types should implement addition (meaning concatenation) and multiplication (meaning repetition)
by defining the methods __add__(), __radd__(), __iadd__(), __mul__(), __rmul__() and __imul__() described below;
they should not define __coerce__() or other numerical operators.
It is recommended that both mappings and sequences implement the __contains__() method
to allow efficient use of the in operator; for mappings, in should be equivalent of has_key();
for sequences, it should search through the values.
It is further recommended that sequences implement the __iter__() method
to allow efficient iteration through the container; for sequences, it should iterate through the values.

If we're interested in .flatten() and also using yield and generators for other recursive functions
http://chimera.labs.oreilly.com/books/1230000000393/ch04.html#_problem_70
http://stackoverflow.com/questions/231767/what-does-the-yield-keyword-do-in-python
"""

import re

class JaggedArray(object):

    def __init__(self, ja=[]):
        self.store = ja
        self.e_count = None
        self._depth = None

    #Intention is to call this when the contents of the JA change, so that counts don't get stale
    def _reinit(self):
        self.e_count = None

    def array(self):
        return self.store

    def sub_array_length(self, indexes=[]):
        """
        :param indexes:  a list of 0 based indexes, for digging len(indexes) levels into the array
        :return: The length of the array at the provided index
        """
        a = self.store
        if len(indexes) == 0:
            return len(a)
        for i in range(0, len(indexes)):
            if indexes[i] > len(a) - 1:
                return None
            a = a[indexes[i]]
        try:
            result = len(a)
        except TypeError:
            result = 0
        return result

    def next_index(self, starting_points):
        """
        Return the next populated address in a JA
        :param starting_points: An array indicating starting address in the JA
        """
        return self._dfs_traverse(self.store, starting_points)

    def prev_index(self, starting_points):
        """
        Return the previous populated address in a JA
        :param starting_points: An array indicating starting address in the JA
        """
        return self._dfs_traverse(self.store, starting_points, False)

    def is_full(self, _cur=None):
        if _cur is None:
            return self.is_full(_cur=self.store)
        if isinstance(_cur, list):
            if not len(_cur):
                return False
            for a in _cur:
                if not self.is_full(a):
                    return False
        else:
            if not _cur:
                return False
        return True

    def is_empty(self, _cur=None):
        if _cur is None:
            return self.is_empty(_cur=self.store)
        if isinstance(_cur, list):
            if not len(_cur):
                return True
            return all([self.is_empty(a) for a in _cur])
        else:
            return not bool(_cur)

    def sections(self, _cur=[]):
        """
        List of valid indexes in this object, to depth one up from bottom
        :param _cur: list of indexes
        :return:
        """

        if self.get_depth() - 1 <= len(_cur):
            return [_cur]
        return reduce(lambda a, b: a + self.sections(b), [_cur + [i] for i in range(self.sub_array_length(_cur))], [])

    def non_empty_sections(self):
        return [s for s in self.sections() if not self.subarray(s).is_empty()]

    def element_count(self):
        if self.e_count is None:
            self.e_count = self._ecnt(self.store)
        return self.e_count if self.e_count else 0

    def _ecnt(self, jta):
        if isinstance(jta, list):
            return sum([self._ecnt(i) for i in jta])
        else:
            return 1

    @staticmethod
    def _dfs_traverse(counts_map, starting_points=None, forward=True, depth=0):
        """
        Private function to recusrsively iterate through the counts doc to find the next available section
        :param counts_map: the counts doc map of available texts
        :param forward: if to move forward or backwards
        :param starting_points: the indices from which to start looking.
        :param depth: tracking parameter for recursion.
        :return: the indices where the next section is at.
        """
        #at the lowest level, we will have either strings or ints indicating text existence or not.
        if isinstance(counts_map, (int, basestring)):
            return bool(counts_map)

        #otherwise iterate through the sections
        else:
            #doesn't matter if we are out of bounds (slicing returns empty arrays for illegal indices)
            if forward:
                #we have been told where to start looking
                if depth < len(starting_points):
                    begin_index = starting_points[depth]
                    #this is in case we come back to this depth, then we want to start from 0 becasue the start point only matters for the
                    #array element we were in to begin with
                    starting_points[depth] = 0
                else:
                    begin_index = 0
                #we are going in order, so we want the next element (we also want to preserve the original indices)
                #TODO: this is a bit of wasted memory allocation, but have not yet found a better way
                section_to_traverse = enumerate(counts_map[begin_index:], begin_index)
            else:
                if depth < len(starting_points):
                    #we want to include the element we are on when going backwards.
                    begin_index = starting_points[depth] + 1 if starting_points[depth] is not None else None
                    #this will make the slice go to the end.
                    starting_points[depth] = None
                else:
                    begin_index = None
                #we are going in reverse, so we want everything up to the current element.
                #this weird hack will preserve the original numeric indices and allow reverse iterating
                section_to_traverse = reversed(list(enumerate(counts_map[:begin_index])))

            for n, j in section_to_traverse:
                result = JaggedArray._dfs_traverse(j, starting_points, forward, depth+1)
                if result:
                    #if we have a result, add the index location to a list that will eventually map to this section.
                    indices = [n] + result if isinstance(result, list) else [n]
                    return indices
            return False

    def mask(self, __curr=None):
        """
        Returns a new jagged array which corresponds in shape to this jagged array,
        with each terminal element populated with 1 or 0
        if a truthy value is present in each position - 1, if not 0.
        :return JaggedIntArray:
        """
        if __curr is None:  # On simple call, return object.
            return JaggedIntArray(self.mask(self.store))
        if isinstance(__curr, list):  # on recursed calls, return array
            return [self.mask(c) for c in __curr]
        else:
            return 0 if not __curr else 1

    def zero_mask(self, __curr=None):
        """
        Returns a jagged array of identical shape to 'array'
        with all elements replaced by 0.
        """
        if __curr is None:  # On simple call, return object.
            return JaggedIntArray(self.zero_mask(self.store))
        if isinstance(__curr, list):
            return [self.zero_mask(c) for c in __curr]
        else:
            return 0

    def get_depth(self):
        if not self._depth:
            self._depth = self.depth()
        return self._depth

    def depth(self, _cur=None, deep=False):
        """
        returns 1 for [], 2 for [[]], etc.
        :parm x - a list
        :param deep - whether or not to count a level when not all elements in
        that level are lists.
        e.g. [[], ""] has a list depth of 1 with depth=False, 2 with depth=True
        """

        if _cur is None:
            return self.depth(_cur=self.store)
        if not isinstance(_cur, list):
            return 0
        elif len(_cur) > 0 and (deep or all(map(lambda y: isinstance(y, list), _cur))):
            return 1 + max([self.depth(y, deep=deep) for y in _cur])
        else:
            return 1

    # derived from TextChunk.trim_text
    def subarray_with_ref(self, ref):
        start = [i - 1 for i in ref.sections]
        end = [i - 1 for i in ref.toSections]
        return self.subarray(start, end)

    # derived from TextChunk.trim_text
    def subarray(self, start_indexes, end_indexes=None):
        """
        Trims a JA to the specifications of start_indexes and end_indexes
        This works on simple Refs and range refs of unlimited depth and complexity.
        :param txt:
        :return: List|String depending on depth of Ref
        """
        if not end_indexes:
            end_indexes = start_indexes

        assert len(start_indexes) == len(end_indexes)
        assert len(start_indexes) <= self.depth
        range_index = len(start_indexes)

        for i in range(0, len(start_indexes)):
            if start_indexes[i] != end_indexes[i]:
                range_index = i
                break
        subarray = self.store[:]
        if not start_indexes:
            pass
        else:
            for i in range(0, len(start_indexes)):
                if range_index > i:  # Either not range, or range begins later.  Return simple value.
                    if len(subarray) > start_indexes[i]:
                        subarray = subarray[start_indexes[i]]
                    else:
                        return self.__class__([])
                elif range_index == i:  # Range begins here
                    start = start_indexes[i]
                    end = end_indexes[i] + 1
                    subarray = subarray[start:end]
                else:  # range_index < i, range continues here
                    begin = end = subarray
                    for _ in range(range_index, i - 1):
                        begin = begin[0]
                        end = end[-1]
                    begin[0] = begin[0][start_indexes[i]:]
                    end[-1] = end[-1][:end_indexes[i] + 1]
        return self.__class__(subarray)

    def __eq__(self, other):
        return self.store == other.store

    def __len__(self):
        return self.sub_array_length()

    def length(self):
        return self.__len__()

class JaggedTextArray(JaggedArray):

    def __init__(self, ja=[]):
        JaggedArray.__init__(self, ja)
        self.w_count = None
        self.c_count = None

    def _reinit(self):
        super(JaggedTextArray, self)._reinit()
        self.w_count = None
        self.c_count = None

    def verse_count(self):
        return self.element_count()

    def word_count(self):
        """ return word count in this JTA """
        if self.w_count is None:
            self.w_count = self._wcnt(self.store)
        return self.w_count if self.w_count else 0

    def _wcnt(self, jta):
        """ Returns the number of characters in an undecorated jagged array """
        if isinstance(jta, basestring):
            return len(jta.split(" "))
        elif isinstance(jta, list):
            return sum([self._wcnt(i) for i in jta])
        else:
            return 0

    def char_count(self):
        """ return character count in this JTA """
        if self.c_count is None:
            self.c_count = self._ccnt(self.store)
        return self.c_count if self.c_count else 0

    def _ccnt(self, jta):
        """ Returns the number of characters in an undecorated jagged array """
        if isinstance(jta, basestring):
            return len(jta)
        elif isinstance(jta, list):
            return sum([self._ccnt(i) for i in jta])
        else:
            return 0

    def trim_ending_whitespace(self, _cur=None):
        if _cur == None:
            self.store = self.trim_ending_whitespace(self.store)
            return self
        if not isinstance(_cur, list): # shouldn't get here
            return _cur
        if not len(_cur):
            return
        if isinstance(_cur[0], list):
            return [self.trim_ending_whitespace(part) for part in _cur]
        else: # depth 1
            final_index = len(_cur) - 1
            for i in range(final_index, -1, -1):
                if not _cur[i] or re.match(r"^\s*$", _cur[i]):
                    final_index = i - 1
                else:
                    break
            if not final_index == len(_cur) - 1:
                _cur = _cur[0:final_index + 1]
            return _cur

    def overlaps(self, other=None, _self_cur=None, _other_cur=None):
        """
        Returns True if self and other contain one or more positions where both are non empty.
        Runs recursively.
        """
        if other:
            return self.overlaps(_self_cur=self.store, _other_cur=other.store)
        if isinstance(_self_cur, list) and isinstance(_other_cur, list):
            for i in range(min(len(_self_cur), len(_other_cur))):
                if self.overlaps(_self_cur=_self_cur[i], _other_cur=_other_cur[i]):
                    return True
        if isinstance(_self_cur, basestring) and isinstance(_other_cur, basestring):
            if _self_cur and _other_cur:
                return True
        return False

class JaggedIntArray(JaggedArray):
    def add(self, other):
        return self.__add__(other)

    def __add__(self, other):
        """
        :return JaggedIntArray:
        """
        assert isinstance(other, JaggedIntArray)
        return JaggedIntArray(self._add(self.store, other.store))

    @staticmethod
    def _add(a, b):
        """
        Returns a multi-dimensional array which sums each position of
        two multidimensional arrays of ints. Missing elements are given 0 value.
        [[1, 2], [3, 4]] + [[2,3], [4]] = [[3, 5], [7, 4]]
        """
        # Treat None as 0
        if a is None:
            return JaggedIntArray._add(0, b)
        if b is None:
            return JaggedIntArray._add(a, 0)

        # If one value is an int while the other is a list,
        # Treat the int as an empty list.
        # Needed e.g, when a whole chapter is missing appears as 0
        if isinstance(a, int) and isinstance(b, list):
            return JaggedIntArray._add([],b)
        if isinstance(b, int) and isinstance(a, list):
            return JaggedIntArray._add(a,[])

        # If both are ints, return the sum
        if isinstance(a, int) and isinstance(b, int):
            return a + b
        # If both are lists, recur on each pair of values
        # map results in None value when element not present
        if isinstance(a, list) and isinstance(b, list):
            return [JaggedIntArray._add(a2, b2) for a2, b2 in map(None, a, b)]

        raise Exception("JaggedIntArray._sum() reached a condition it shouldn't have reached")

    def depth_sum(self, depth):
        return self._depth_sum(self.store, depth)

    @staticmethod
    def _depth_sum(curr, depth):
        """
        Sum the counts of a text at given depth to get the total number of a given kind of section
        E.g, for counts on all of Job, depth 0 counts chapters, depth 1 counts verses
        """
        if depth == 0:
            if isinstance(curr, int):
                return min(curr, 1)
            else:
                sum = 0
                for i in range(len(curr)):
                    sum += min(JaggedIntArray._depth_sum(curr[i], 0), 1)
                return sum
        else:
            sum = 0
            for i in range(len(curr)):
                sum += JaggedIntArray._depth_sum(curr[i], depth - 1)
            return sum