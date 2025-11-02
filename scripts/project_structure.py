from pathlib import Path


def generate_folder_structure(path, exclusions, output_file):
    """Generate a tree-style folder structure with enhanced presentation."""

    # Comments for different paths
    comments = {
        '.github/workflows': '# CI/CD automation',
        'scripts': '# Utility scripts and tools',
        'src/puzzle_solver/api': '# FastAPI web interface',
        'src/puzzle_solver/cli': '# Command-line interface',
        'src/puzzle_solver/clients': '# HTTP client management',
        'src/puzzle_solver/config': '# Configuration and settings',
        'src/puzzle_solver/core': '# Logging and core utilities',
        'src/puzzle_solver/domain/models': '# Data models (Fragment, FragmentBatch)',
        'src/puzzle_solver/domain/services': '# Business logic (PuzzleService, FragmentService)',
        'src/puzzle_solver/utils': '# Utility functions',
        'tests/unit': '# Unit tests'
    }

    def get_comment(path_parts):
        path_str = '/'.join(path_parts)
        return comments.get(path_str, '')

    def get_tree_prefix(is_last, level):
        if level == 0:
            return ""
        return "│   " * (level - 1) + ("└── " if is_last else "├── ")

    def write_directory_tree(f, current_path, level=0, is_last=True, path_parts=[]):
        if level > 0:  # Skip root directory name
            prefix = get_tree_prefix(is_last, level)
            comment = get_comment(path_parts)
            f.write(f"{prefix}{current_path.name}/ {comment}\n")

        try:
            items = sorted(current_path.iterdir(), key=lambda x: (x.is_file(), x.name.lower()))
            dirs = [item for item in items if item.is_dir() and item.name not in exclusions]
            files = [item for item in items if item.is_file()]

            # Write directories first
            for i, dir_path in enumerate(dirs):
                is_last_dir = (i == len(dirs) - 1) and len(files) == 0
                new_path_parts = path_parts + [dir_path.name]
                write_directory_tree(f, dir_path, level + 1, is_last_dir, new_path_parts)

            # Write files
            for i, file_path in enumerate(files):
                is_last_file = i == len(files) - 1
                prefix = get_tree_prefix(is_last_file, level + 1)
                f.write(f"{prefix}{file_path.name}\n")

        except PermissionError:
            pass

    base_path = Path(path).resolve()

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"{base_path.name}/\n")
        write_directory_tree(f, base_path, path_parts=[])


if __name__ == "__main__":
    base_path = r'..'
    exclusions = ['.venv', '.idea', '__pycache__', '.git', 'node_modules', '.pytest_cache']
    output_file = 'folder_structure.txt'

    print("Generating project structure...")
    generate_folder_structure(base_path, exclusions, output_file)
    print(f"Structure saved to: {output_file}")

    # Also print to console
    with open(output_file, 'r', encoding='utf-8') as f:
        print("\n" + f.read())
