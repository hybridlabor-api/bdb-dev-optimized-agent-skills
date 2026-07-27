import unittest

import src.server as compound


class MediaPoolItemStub:
    def __init__(self, file_path):
        self.file_path = file_path

    def GetClipProperty(self, key):
        if key == "File Path":
            return self.file_path
        return None


class TimelineItemStub:
    def __init__(
        self,
        *,
        name="Timeline Item",
        file_path="/tmp/synthetic_source.mov",
        start=86400,
        end=86448,
        left_offset=0,
        unique_id="timeline-item-1",
    ):
        self.name = name
        self.media_pool_item = MediaPoolItemStub(file_path)
        self.start = start
        self.end = end
        self.left_offset = left_offset
        self.unique_id = unique_id

    def GetName(self):
        return self.name

    def GetMediaPoolItem(self):
        return self.media_pool_item

    def GetStart(self):
        return self.start

    def GetEnd(self):
        return self.end

    def GetLeftOffset(self):
        return self.left_offset

    def GetUniqueId(self):
        return self.unique_id


class TimelineStub:
    def __init__(self, items):
        self.items = items

    def GetName(self):
        return "source_ranges_timeline"

    def GetTrackCount(self, track_type):
        return 1 if track_type == "video" else 0

    def GetItemListInTrack(self, track_type, track_index):
        if track_type == "video" and track_index == 1:
            return self.items
        return []


class ProjectStub:
    def __init__(self, timeline):
        self.timeline = timeline

    def GetCurrentTimeline(self):
        return self.timeline


class ExtractSourceFrameRangesTest(unittest.TestCase):
    def setUp(self):
        self.original_check = compound._check

    def tearDown(self):
        compound._check = self.original_check

    def _install_timeline(self, items):
        timeline = TimelineStub(items)
        project = ProjectStub(timeline)
        compound._check = lambda: (None, project, None)
        return timeline

    def test_handles_zero_keeps_inclusive_end_on_last_used_frame(self):
        self._install_timeline(
            [
                TimelineItemStub(
                    file_path="/media/synthetic_48_frame_clip.mov",
                    start=86400,
                    end=86448,
                    left_offset=0,
                )
            ]
        )

        out = compound.timeline("extract_source_frame_ranges", {"handles": 0})

        self.assertEqual(out["clip_count"], 1)
        self.assertEqual(out["occurrences"][0]["source_used_inclusive_end"], 47)
        self.assertEqual(out["occurrences"][0]["source_range_final"], [0, 47])
        self.assertEqual(out["frame_ranges"], {"synthetic_48_frame_clip.mov": [[0, 47]]})

    def test_fixed_handles_extend_from_inclusive_used_range(self):
        self._install_timeline(
            [
                TimelineItemStub(
                    file_path="/media/synthetic_48_frame_clip.mov",
                    start=86400,
                    end=86448,
                    left_offset=12,
                )
            ]
        )

        out = compound.timeline("extract_source_frame_ranges", {"handles": 8})

        self.assertEqual(out["occurrences"][0]["source_used_inclusive_end"], 59)
        self.assertEqual(out["occurrences"][0]["source_range_final"], [4, 67])
        self.assertEqual(out["frame_ranges"], {"synthetic_48_frame_clip.mov": [[4, 67]]})


if __name__ == "__main__":
    unittest.main()
