import unittest

from vg.research.windows_client_strings import decode_rtti, readable_runs


class WindowsClientStringTests(unittest.TestCase):
    def test_simple_rtti_is_decoded(self):
        self.assertEqual(
            decode_rtti(".?AVKindredReplay@Kindred@Nuo@@"),
            "Nuo::Kindred::KindredReplay",
        )

    def test_template_rtti_is_not_decoded(self):
        raw = (".?AV?$GameplayBehavior_ChangeNavMeshOnSelection_Instance"
               "@ULocalBehaviorContext@@")
        self.assertIsNone(decode_rtti(raw))

    def test_nested_class_rtti_is_decoded(self):
        self.assertEqual(
            decode_rtti(".?AUReplayAnnotationNode@KindredSpectatorHUDReplay@Kindred@Nuo@@"),
            "Nuo::Kindred::KindredSpectatorHUDReplay::ReplayAnnotationNode",
        )

    def test_function_scope_rtti_is_not_decoded(self):
        self.assertIsNone(decode_rtti(".?AVLocal@?1??Foo@@YAXXZ@"))

    def test_ascii_and_utf16le_runs_are_read(self):
        data = b"VaingloryReplay.dat\0" + "PktImpactHealth".encode("utf-16-le")
        runs = readable_runs(data)
        self.assertIn((0, "VaingloryReplay.dat", "ascii"), runs)
        self.assertTrue(any(value == "PktImpactHealth" and encoding == "utf-16-le"
                            for _, value, encoding in runs))


if __name__ == "__main__":
    unittest.main()
