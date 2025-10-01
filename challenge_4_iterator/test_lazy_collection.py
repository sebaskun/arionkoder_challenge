"""
Tests for LazyCollection - Custom Iterator with Lazy Evaluation

Essential tests covering:
1. Lazy evaluation behavior
2. Core operations (map, filter, chunk, reduce, take)
3. Chaining operations
4. Memory efficiency
5. Edge cases
"""

from lazy_collection import LazyCollection


class TestLazyEvaluation:
    """Test that operations don't execute until iteration."""

    def test_chained_operations_are_lazy(self):
        """Chained operations should not execute until iteration."""
        map_calls = 0
        filter_calls = 0

        def track_map(x):
            nonlocal map_calls
            map_calls += 1
            return x * 2

        def track_filter(x):
            nonlocal filter_calls
            filter_calls += 1
            return x > 5

        # Chain operations
        lc = (
            LazyCollection([1, 2, 3, 4, 5])
            .map(track_map)
            .filter(track_filter)
        )

        # Neither should have executed yet
        assert map_calls == 0
        assert filter_calls == 0

        # Now iterate
        result = lc.to_list()
        assert result == [6, 8, 10]
        assert map_calls == 5
        assert filter_calls == 5


class TestBasicOperations:
    """Test core operations work correctly."""

    def test_map(self):
        """Map should transform each element."""
        result = LazyCollection([1, 2, 3]).map(lambda x: x * 2).to_list()
        assert result == [2, 4, 6]

    def test_filter(self):
        """Filter should keep only matching elements."""
        result = (
            LazyCollection([1, 2, 3, 4, 5, 6])
            .filter(lambda x: x % 2 == 0)
            .to_list()
        )
        assert result == [2, 4, 6]

    def test_reduce_sum(self):
        """Reduce to sum."""
        result = LazyCollection([1, 2, 3, 4, 5]).reduce(lambda acc, x: acc + x, 0)
        assert result == 15

    def test_reduce_without_initial(self):
        """Reduce without initial value."""
        result = LazyCollection([1, 2, 3, 4]).reduce(lambda acc, x: acc + x)
        assert result == 10

    def test_take(self):
        """Take first N elements."""
        result = LazyCollection([1, 2, 3, 4, 5]).take(3).to_list()
        assert result == [1, 2, 3]


class TestChunking:
    """Test chunking functionality."""

    def test_chunk_even_division(self):
        """Chunking with even division."""
        result = LazyCollection([1, 2, 3, 4, 5, 6]).chunk(2).to_list()
        assert result == [[1, 2], [3, 4], [5, 6]]

    def test_chunk_uneven_division(self):
        """Chunking with remainder."""
        result = LazyCollection([1, 2, 3, 4, 5]).chunk(2).to_list()
        assert result == [[1, 2], [3, 4], [5]]


class TestChaining:
    """Test chaining multiple operations."""

    def test_map_then_filter(self):
        """Should chain map and filter."""
        result = (
            LazyCollection([1, 2, 3, 4, 5])
            .map(lambda x: x * 2)      # [2, 4, 6, 8, 10]
            .filter(lambda x: x > 5)   # [6, 8, 10]
            .to_list()
        )
        assert result == [6, 8, 10]

    def test_complex_chain(self):
        """Should handle complex chains."""
        result = (
            LazyCollection(range(20))
            .filter(lambda x: x % 2 == 0)   # Evens
            .map(lambda x: x * 3)            # Triple
            .filter(lambda x: x < 30)        # < 30
            .map(lambda x: x + 1)            # Add 1
            .to_list()
        )
        assert result == [1, 7, 13, 19, 25]


class TestMemoryEfficiency:
    """Test that memory usage is efficient."""

    def test_take_efficiency(self):
        """Take should not process unnecessary elements."""
        call_count = 0

        def track_calls(x):
            nonlocal call_count
            call_count += 1
            return x * 2

        result = (
            LazyCollection(range(1000))
            .map(track_calls)
            .take(5)
            .to_list()
        )

        assert result == [0, 2, 4, 6, 8]
        # Note: call_count might be 6 due to the way generators work
        # (checking if there's a next element), which is still efficient
        assert call_count <= 10  # Should process ~5 elements, not 1000!

    def test_large_range_with_take(self):
        """Should not consume all memory for large ranges when using take."""
        # If this was eager, it would create a huge list
        # With lazy evaluation, we only process what we need
        result = (
            LazyCollection(range(10_000_000))
            .map(lambda x: x ** 2)
            .filter(lambda x: x % 2 == 0)
            .take(10)
            .to_list()
        )
        assert len(result) == 10
        assert result[0] == 0
        assert result[1] == 4


class TestIteration:
    """Test iteration behavior."""

    def test_for_loop(self):
        """Should work with for loops."""
        result = []
        for item in LazyCollection([1, 2, 3]).map(lambda x: x * 2):
            result.append(item)
        assert result == [2, 4, 6]


class TestEdgeCases:
    """Test edge cases."""

    def test_empty_collection(self):
        """Should handle empty collections."""
        result = LazyCollection([]).map(lambda x: x * 2).filter(lambda x: x > 0).to_list()
        assert result == []

    def test_take_zero(self):
        """Take zero elements."""
        result = LazyCollection([1, 2, 3]).take(0).to_list()
        assert result == []

    def test_chunk_empty_collection(self):
        """Chunking empty collection."""
        result = LazyCollection([]).chunk(2).to_list()
        assert result == []
