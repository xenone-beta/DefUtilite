#!/usr/bin/env python3
"""DefUtilite — универсальная утилита для базового обслуживания файлов и папок."""

from __future__ import annotations

import argparse
import fnmatch
import os
import shutil
import stat
from pathlib import Path
from typing import Iterable


def _on_rm_error(func, path, exc_info):
    """Обработчик ошибок удаления: пытается снять read-only флаг и повторить."""
    os.chmod(path, stat.S_IWRITE)
    func(path)


def find_paths(root: Path, pattern: str, include_dirs: bool = True) -> list[Path]:
    """Ищет файлы/папки по шаблону имени (поддержка wildcard, например *.log)."""
    matches: list[Path] = []

    for current_root, dirs, files in os.walk(root):
        current_root_path = Path(current_root)

        if include_dirs:
            for directory in dirs:
                if fnmatch.fnmatch(directory, pattern):
                    matches.append(current_root_path / directory)

        for file_name in files:
            if fnmatch.fnmatch(file_name, pattern):
                matches.append(current_root_path / file_name)

    return sorted(matches)


def delete_paths(paths: Iterable[Path], dry_run: bool = False) -> tuple[int, int]:
    """Удаляет переданные пути. Возвращает (удалено, ошибок)."""
    deleted = 0
    errors = 0

    for path in paths:
        try:
            if dry_run:
                print(f"[DRY-RUN] Удалил бы: {path}")
                deleted += 1
                continue

            if path.is_dir():
                shutil.rmtree(path, onerror=_on_rm_error)
            else:
                path.unlink(missing_ok=True)
            print(f"Удалено: {path}")
            deleted += 1
        except Exception as exc:  # pragma: no cover
            print(f"Ошибка удаления {path}: {exc}")
            errors += 1

    return deleted, errors


def delete_by_name(root: Path, pattern: str, dry_run: bool = False) -> int:
    """Быстрое удаление файлов/папок по имени из выбранного корня."""
    paths = find_paths(root, pattern, include_dirs=True)
    if not paths:
        print("Ничего не найдено.")
        return 0

    print(f"Найдено объектов: {len(paths)}")
    deleted, errors = delete_paths(paths, dry_run=dry_run)
    print(f"Итог: удалено={deleted}, ошибок={errors}")
    return 0 if errors == 0 else 1


def calculate_folder_size(root: Path) -> int:
    """Считает размер папки в байтах."""
    total = 0
    for current_root, _dirs, files in os.walk(root):
        for file_name in files:
            file_path = Path(current_root) / file_name
            try:
                total += file_path.stat().st_size
            except OSError:
                continue
    return total


def human_size(size: int) -> str:
    """Преобразует байты в читабельный формат."""
    units = ["B", "KB", "MB", "GB", "TB"]
    result = float(size)
    for unit in units:
        if result < 1024 or unit == units[-1]:
            return f"{result:.2f} {unit}"
        result /= 1024
    return f"{size} B"


def remove_empty_dirs(root: Path, dry_run: bool = False) -> tuple[int, int]:
    """Удаляет пустые папки снизу вверх."""
    removed = 0
    errors = 0

    for current_root, dirs, _files in os.walk(root, topdown=False):
        for directory in dirs:
            target = Path(current_root) / directory
            try:
                if any(target.iterdir()):
                    continue

                if dry_run:
                    print(f"[DRY-RUN] Удалил бы пустую папку: {target}")
                else:
                    target.rmdir()
                    print(f"Удалена пустая папка: {target}")
                removed += 1
            except Exception as exc:  # pragma: no cover
                print(f"Ошибка удаления папки {target}: {exc}")
                errors += 1

    return removed, errors


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="DefUtilite",
        description="DefUtilite — утилита с набором полезных функций для ПК.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    delete_parser = subparsers.add_parser(
        "delete-name", help="Удалить файлы/папки по имени или маске имени."
    )
    delete_parser.add_argument("pattern", help="Имя или маска (*.tmp, cache*, report.txt)")
    delete_parser.add_argument("--root", default=".", help="Корневая папка для поиска")
    delete_parser.add_argument("--dry-run", action="store_true", help="Показать, что удалится")

    find_parser = subparsers.add_parser(
        "find", help="Найти файлы/папки по имени или маске имени."
    )
    find_parser.add_argument("pattern", help="Имя или маска (*.log, backup*)")
    find_parser.add_argument("--root", default=".", help="Корневая папка поиска")

    size_parser = subparsers.add_parser(
        "folder-size", help="Показать общий размер папки."
    )
    size_parser.add_argument("path", help="Путь к папке")

    cleanup_parser = subparsers.add_parser(
        "cleanup-empty", help="Удалить пустые папки внутри указанной директории."
    )
    cleanup_parser.add_argument("--root", default=".", help="Корневая папка очистки")
    cleanup_parser.add_argument("--dry-run", action="store_true", help="Показать, что удалится")

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "delete-name":
        return delete_by_name(Path(args.root), args.pattern, dry_run=args.dry_run)

    if args.command == "find":
        matches = find_paths(Path(args.root), args.pattern, include_dirs=True)
        if not matches:
            print("Ничего не найдено.")
            return 0

        for item in matches:
            print(item)
        print(f"Всего найдено: {len(matches)}")
        return 0

    if args.command == "folder-size":
        target = Path(args.path)
        if not target.exists() or not target.is_dir():
            print(f"Папка не найдена: {target}")
            return 1

        size = calculate_folder_size(target)
        print(f"Размер папки {target}: {human_size(size)} ({size} bytes)")
        return 0

    if args.command == "cleanup-empty":
        removed, errors = remove_empty_dirs(Path(args.root), dry_run=args.dry_run)
        print(f"Итог: удалено пустых папок={removed}, ошибок={errors}")
        return 0 if errors == 0 else 1

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
