from pathlib import Path


def verify_folder(folder: Path):
    for element in folder.iterdir():
        print(element)
        if element.is_dir():
            verify_folder(element)
        elif element.name.endswith('.py'):
            with element.open('r') as fp:
                lines = fp.readlines()
            imports = filter(lambda x: 'import' in x, lines)
            mouse_imports = filter(
                lambda x: ' controller' in x or ' model' in x or ' view' in x,
                imports)
            bad_imports = list(
                filter(lambda x: ' mouseapp' not in x, mouse_imports))
            assert bad_imports == [], element


def test_importing():
    src = Path(__file__).parent.parent.joinpath('src')
    verify_folder(src)
