import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('recipe', ROOT / 'generate_device_recipe.py')
recipe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(recipe)


class PackageSelectionTests(unittest.TestCase):
    def setUp(self):
        self.work = tempfile.TemporaryDirectory()
        self.root = Path(self.work.name)
        self.previous = recipe.BUILDER_MAIN_DIRECTORY
        recipe.BUILDER_MAIN_DIRECTORY = str(self.root)
        (self.root / 'apt').mkdir()

    def tearDown(self):
        recipe.BUILDER_MAIN_DIRECTORY = self.previous
        self.work.cleanup()

    def package(self, name, version, architecture='arm64'):
        directory = self.root / f'{name}-{version}-{architecture}'
        (directory / 'DEBIAN').mkdir(parents=True)
        (directory / 'DEBIAN/control').write_text(
            f'Package: {name}\nVersion: {version}\nArchitecture: {architecture}\n'
            'Maintainer: Test <test@example.com>\nDescription: package selection fixture\n')
        subprocess.run(['dpkg-deb', '--build', '--root-owner-group', str(directory),
                        str(self.root / 'apt' / f'{name}_{version}_{architecture}.deb')],
                       check=True, capture_output=True)

    def test_device_and_camera_versions_are_explicit(self):
        self.package('droidian-camera', '16+t870.1')
        self.package('adaptation-samsung-gts7lwifi', '0.0.3', 'all')
        self.assertEqual(recipe.local_package_specs(
            ['droidian-camera', 'adaptation-samsung-gts7lwifi', 'bluez'], 'arm64'),
            ['droidian-camera=16+t870.1', 'adaptation-samsung-gts7lwifi=0.0.3', 'bluez'])

    def test_foreign_architecture_is_ignored(self):
        self.package('droidian-camera', '16+t870.1', 'amd64')
        self.assertEqual(recipe.local_package_specs(['droidian-camera'], 'arm64'),
                         ['droidian-camera'])

    def test_multiple_versions_are_rejected(self):
        self.package('droidian-camera', '16+t870.1')
        self.package('droidian-camera', '16+t870.2')
        with self.assertRaises(ValueError):
            recipe.local_package_specs(['droidian-camera'], 'arm64')


if __name__ == '__main__':
    unittest.main()
