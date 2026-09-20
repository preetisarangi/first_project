"""Knowledge Base Ingestion Pipeline.

Parses Playwright TypeScript Page Objects, helpers, and test specs,
generates 384-dimensional dense embeddings using FastEmbed (BAAI/bge-small-en-v1.5),
and stores them in the Supabase test_knowledge_base table.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from fastembed import TextEmbedding
except ImportError:
    TextEmbedding = None  # type: ignore

from src.db.supabase_client import get_supabase_client

EMBEDDING_MODEL_NAME = "BAAI/bge-small-en-v1.5"
EMBEDDING_DIM = 384


@dataclass
class CodeChunk:
    file_path: str
    chunk_type: str  # 'page_object', 'utility', 'spec_pattern'
    content: str
    metadata: Dict[str, Any]


class KnowledgeIngestionPipeline:
    def __init__(self, model_name: str = EMBEDDING_MODEL_NAME):
        self.model_name = model_name
        self._embedder: Optional[Any] = None

    @property
    def embedder(self) -> Any:
        if self._embedder is None:
            if TextEmbedding is None:
                raise RuntimeError(
                    "The 'fastembed' library is not installed. "
                    "Please install it using 'pip install fastembed'."
                )
            print(f"[*] Initializing FastEmbed model '{self.model_name}' on CPU...")
            self._embedder = TextEmbedding(model_name=self.model_name)
        return self._embedder

    def extract_chunks_from_file(self, file_path: Path, base_dir: Path) -> List[CodeChunk]:
        """Parse a TypeScript / Playwright file into semantic code chunks."""
        relative_path = str(file_path.relative_to(base_dir))
        content = file_path.read_text(encoding="utf-8")
        chunks: List[CodeChunk] = []

        is_spec = file_path.name.endswith(".spec.ts") or file_path.name.endswith(".test.ts")
        is_page = "page" in file_path.name.lower() or "pages" in file_path.parts

        if is_spec:
            # Extract individual test blocks or describe suites
            test_matches = list(re.finditer(
                r"(test(?:\.(?:skip|only|fixme))?\s*\(\s*['\"`](.+?)['\"`]\s*,\s*async\s*\([^)]*\)\s*=>\s*\{[\s\S]*?\n\}\);)",
                content
            ))
            if test_matches:
                for match in test_matches:
                    snippet = match.group(1).strip()
                    test_title = match.group(2).strip()
                    chunks.append(
                        CodeChunk(
                            file_path=relative_path,
                            chunk_type="spec_pattern",
                            content=snippet,
                            metadata={
                                "file_name": file_path.name,
                                "test_title": test_title,
                                "type": "spec_pattern",
                            },
                        )
                    )
            else:
                # Fallback: store whole spec if individual tests not isolated
                chunks.append(
                    CodeChunk(
                        file_path=relative_path,
                        chunk_type="spec_pattern",
                        content=content.strip(),
                        metadata={"file_name": file_path.name, "type": "spec_pattern"},
                    )
                )

        elif is_page:
            # Extract Class definition, locator maps, and action methods
            class_match = re.search(r"export\s+class\s+(\w+)\s*\{([\s\S]*)\}", content)
            if class_match:
                class_name = class_match.group(1)
                body = class_match.group(2)

                # 1. Locator definitions chunk
                locators = re.findall(
                    r"(?:readonly\s+)?(\w+)\s*=\s*(?:this\.page\.(?:locator|getBy\w+)\([^)]*\)|.*?);",
                    body,
                )
                if locators:
                    locator_text = f"// Page Object Locators for {class_name}\n" + "\n".join(
                        line.strip() for line in body.splitlines() if "locator" in line or "getBy" in line
                    )
                    chunks.append(
                        CodeChunk(
                            file_path=relative_path,
                            chunk_type="page_object",
                            content=locator_text.strip(),
                            metadata={
                                "file_name": file_path.name,
                                "class_name": class_name,
                                "subtype": "locators",
                            },
                        )
                    )

                # 2. Entire Page Object as comprehensive pattern
                chunks.append(
                    CodeChunk(
                        file_path=relative_path,
                        chunk_type="page_object",
                        content=content.strip(),
                        metadata={
                            "file_name": file_path.name,
                            "class_name": class_name,
                            "subtype": "full_page_object",
                        },
                    )
                )
            else:
                chunks.append(
                    CodeChunk(
                        file_path=relative_path,
                        chunk_type="page_object",
                        content=content.strip(),
                        metadata={"file_name": file_path.name, "type": "page_object"},
                    )
                )
        else:
            # General helper / utility functions
            func_matches = list(re.finditer(
                r"(export\s+(?:async\s+)?function\s+(\w+)\s*\([^)]*\)[\s\S]*?\n\})",
                content
            ))
            if func_matches:
                for match in func_matches:
                    fn_code = match.group(1).strip()
                    fn_name = match.group(2).strip()
                    chunks.append(
                        CodeChunk(
                            file_path=relative_path,
                            chunk_type="utility",
                            content=fn_code,
                            metadata={"file_name": file_path.name, "function_name": fn_name},
                        )
                    )
            else:
                chunks.append(
                    CodeChunk(
                        file_path=relative_path,
                        chunk_type="utility",
                        content=content.strip(),
                        metadata={"file_name": file_path.name, "type": "utility"},
                    )
                )

        return chunks

    def scan_directory(self, target_dir: str | Path) -> List[CodeChunk]:
        """Recursively scan target directory for .ts and .spec.ts files."""
        target_path = Path(target_dir).resolve()
        if not target_path.exists():
            raise FileNotFoundError(f"Target directory '{target_path}' does not exist.")

        all_chunks: List[CodeChunk] = []
        ts_files = list(target_path.rglob("*.ts"))

        print(f"[*] Discovered {len(ts_files)} TypeScript files in {target_path}")
        for ts_file in ts_files:
            # Skip node_modules or dist folders
            if "node_modules" in ts_file.parts or ".next" in ts_file.parts:
                continue
            try:
                chunks = self.extract_chunks_from_file(ts_file, target_path)
                all_chunks.extend(chunks)
            except Exception as e:
                print(f"[!] Warning: Failed to parse '{ts_file}': {e}", file=sys.stderr)

        return all_chunks

    def ingest(self, target_dir: str | Path) -> int:
        """Scan, embed, and upsert all code chunks into Supabase."""
        # 1. Scrape code chunks
        chunks = self.scan_directory(target_dir)
        if not chunks:
            print("[*] No code chunks found to ingest.")
            return 0

        print(f"[*] Extracted {len(chunks)} semantic code chunks. Generating embeddings...")

        # 2. Generate embeddings locally via FastEmbed
        texts_to_embed = [
            f"[{c.chunk_type.upper()}] in {c.file_path}:\n{c.content}"
            for c in chunks
        ]
        embeddings = list(self.embedder.embed(texts_to_embed))

        # 3. Connect to Supabase
        supabase = get_supabase_client()

        # 4. Upsert records into Supabase test_knowledge_base
        records_to_insert = []
        for chunk, embedding in zip(chunks, embeddings):
            # FastEmbed outputs numpy array or float list
            emb_list = embedding.tolist() if hasattr(embedding, "tolist") else list(embedding)
            records_to_insert.append({
                "file_path": chunk.file_path,
                "chunk_type": chunk.chunk_type,
                "content": chunk.content,
                "metadata": chunk.metadata,
                "embedding": emb_list,
            })

        print(f"[*] Upserting {len(records_to_insert)} records into Supabase 'test_knowledge_base'...")
        try:
            # Insert in batches of 50
            batch_size = 50
            for i in range(0, len(records_to_insert), batch_size):
                batch = records_to_insert[i : i + batch_size]
                supabase.table("test_knowledge_base").insert(batch).execute()

            print(f"[✓] Successfully ingested {len(records_to_insert)} chunks into Supabase!")
            return len(records_to_insert)
        except Exception as exc:
            raise RuntimeError(
                f"Failed to upsert embeddings to Supabase: {exc}. "
                "Ensure schema.sql has been executed in your Supabase SQL editor."
            ) from exc


def main():
    parser = argparse.ArgumentParser(
        description="Ingest Playwright Page Objects and Specs into Supabase pgvector."
    )
    parser.add_argument(
        "--target",
        "-t",
        default=str(Path(__file__).parents[3] / "packages" / "test-fixtures"),
        help="Target directory to scan for TypeScript patterns (default: packages/test-fixtures)",
    )
    args = parser.parse_args()

    pipeline = KnowledgeIngestionPipeline()
    try:
        pipeline.ingest(args.target)
    except Exception as err:
        print(f"\n[ERROR] Ingestion failed: {err}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
