from setuptools import setup, find_packages

DOC = ""
with open("README.md", "rt", encoding="utf-8") as f: 
  DOC = f.read()

# Remove __pycache__ everywhere
def clean_pycache(path="."):
  """Clean __pycache__ directories recursively. Call this before setup()."""
  import os
  for file in os.listdir(path):
    new_path = os.path.join(path, file)
    if os.path.isdir(new_path): 
      if file == "__pycache__": 
        # Remove a file or a directory recursively using terminal commands.
        # This way avoid some permissions errors.
        if os.name == "nt": os.system(("rd /s" if os.path.isdir(new_path) else "del /f") + " /q \"" + new_path.replace('/', '\\') + "\"")
        else: os.system("rm -rf \"" + new_path.replace('\\', '/') + "\"")
      else: clean_pycache(new_path)

clean_pycache()
setup(
  name = 'queue_leu_leu', 
  version = '1.0', 
  author = 'ZetaMap', 
  description = 'Collection of Python scripts, showing minimal examples of objects following each other.', 
  license = 'MIT', 
  long_description = DOC, 
  long_description_content_type = 'text/markdown', 
  url = 'https://github.com/xorblo-doitus/queue_leu_leu', 
  project_urls = {
    'GitHub Project': 'https://github.com/xorblo-doitus/queue_leu_leu', 
    'ZetaMap': 'https://github.com/ZetaMap/',
    'xorblo-doitus': 'https://github.com/xorblo-doitus',
  }, 
  classifiers = [
    'Programming Language :: Python :: 3', 
    'License :: OSI Approved :: MIT License', 
    'Operating System :: Microsoft :: Windows', 
    'Operating System :: Unix', 
    'Operating System :: MacOS :: MacOS X',
  ], 
  package_dir = {"": "src"},
  packages = find_packages("src"),
  package_data = {"": ["**"]},
  install_requires = ["pygame"], 
)
