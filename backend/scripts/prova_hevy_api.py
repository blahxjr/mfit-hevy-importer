"""
Prova de Conceito — API Hevy
Valida endpoints de leitura e captura schemas reais.

Uso:
    cd backend
    python scripts/prova_hevy_api.py

Requer:
    - .env com HEVY_API_KEY preenchida
    - Assinatura Hevy Pro (API restrita a Pro)
"""

import os
import sys
import json
import asyncio
from pathlib import Path
from typing import Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

import httpx
from dotenv import load_dotenv

# Carregar .env
load_dotenv()

BASE_URL = os.getenv("HEVY_API_BASE_URL", "https://api.hevyapp.com")
API_KEY = os.getenv("HEVY_API_KEY")
TIMEOUT = int(os.getenv("HEVY_API_TIMEOUT", "30"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")


def schema_snapshot(value: Any, depth: int = 0) -> Any:
    """Retorna campos e tipos de uma resposta sem persistir valores da conta."""
    if depth >= 3:
        return type(value).__name__
    if isinstance(value, dict):
        return {key: schema_snapshot(item, depth + 1) for key, item in value.items()}
    if isinstance(value, list):
        return [schema_snapshot(value[0], depth + 1)] if value else []
    return type(value).__name__


@dataclass
class ApiProvaResult:
    """Resultado de uma chamada à API"""
    endpoint: str
    method: str
    status_code: int
    success: bool
    error: Optional[str] = None
    item_count: int = 0
    sample_item: Optional[dict] = None
    headers: Optional[dict] = None
    timestamp: str = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow().isoformat()


class HevyApiProver:
    """Testador de API Hevy"""

    def __init__(self):
        self.base_url = BASE_URL
        self.headers = {
            "api-key": API_KEY,
            "Content-Type": "application/json",
        }
        self.results = []
        self.session = None

    async def __aenter__(self):
        self.session = httpx.AsyncClient(
            base_url=self.base_url,
            headers=self.headers,
            timeout=TIMEOUT,
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.aclose()

    async def test_endpoint(
        self,
        method: str,
        path: str,
        expected_status: int = 200,
        payload: Optional[dict] = None,
        description: str = "",
    ) -> ApiProvaResult:
        """Testa um endpoint e captura resultado"""

        print(f"\n🔍 Testando: {method} {path}")
        if description:
            print(f"   {description}")

        try:
            if method.upper() == "GET":
                response = await self.session.get(path)
            elif method.upper() == "POST":
                response = await self.session.post(path, json=payload or {})
            elif method.upper() == "PUT":
                response = await self.session.put(path, json=payload or {})
            else:
                raise ValueError(f"Método {method} não suportado")

            success = response.status_code == expected_status
            data = None
            item_count = 0
            sample_item = None

            try:
                data = response.json()
                if isinstance(data, list):
                    item_count = len(data)
                    sample_item = schema_snapshot(data)
                elif isinstance(data, dict):
                    # Tentar entender estrutura
                    if "data" in data:
                        items = data["data"]
                        if isinstance(items, list):
                            item_count = len(items)
                    else:
                        collection = next(
                            (value for value in data.values() if isinstance(value, list)),
                            None,
                        )
                        if collection is not None:
                            item_count = len(collection)
                    sample_item = schema_snapshot(data)
            except json.JSONDecodeError:
                pass

            error_msg = None
            if not success:
                error_msg = f"Status {response.status_code}: {response.text[:200]}"

            print(f"   Status: {response.status_code} {'✅' if success else '❌'}")
            if item_count > 0:
                print(f"   Items: {item_count}")
            if error_msg:
                print(f"   Erro: {error_msg}")

            result = ApiProvaResult(
                endpoint=path,
                method=method.upper(),
                status_code=response.status_code,
                success=success,
                error=error_msg,
                item_count=item_count,
                sample_item=sample_item,
                headers={
                    k: v
                    for k, v in response.headers.items()
                    if k.lower() in ["content-type", "retry-after", "x-ratelimit-remaining"]
                },
            )
            self.results.append(result)
            return result

        except httpx.AuthError as e:
            print(f"   ❌ Erro de Autenticação: {e}")
            result = ApiProvaResult(
                endpoint=path,
                method=method.upper(),
                status_code=401,
                success=False,
                error=f"Auth Error: {str(e)}",
            )
            self.results.append(result)
            return result

        except httpx.HTTPError as e:
            print(f"   ❌ Erro HTTP: {e}")
            result = ApiProvaResult(
                endpoint=path,
                method=method.upper(),
                status_code=0,
                success=False,
                error=f"HTTP Error: {str(e)}",
            )
            self.results.append(result)
            return result

        except Exception as e:
            print(f"   ❌ Erro Inesperado: {e}")
            result = ApiProvaResult(
                endpoint=path,
                method=method.upper(),
                status_code=0,
                success=False,
                error=f"Unexpected Error: {str(e)}",
            )
            self.results.append(result)
            return result

    async def run_prova_completa(self):
        """Executa todas as provas de API"""

        print("\n" + "=" * 70)
        print("PROVA DE CONCEITO — API HEVY")
        print("=" * 70)
        print(f"Base URL: {self.base_url}")
        print(f"Timeout: {TIMEOUT}s")
        print(f"API Key: {'*' * 20}...{API_KEY[-4:] if API_KEY else 'NÃO CONFIGURADA'}")
        print("=" * 70)

        # 1. Exercise Templates (GET)
        await self.test_endpoint(
            "GET",
            "/v1/exercise_templates",
            expected_status=200,
            description="Lista templates de exercícios disponíveis",
        )

        # 2. Routine Folders (GET)
        await self.test_endpoint(
            "GET",
            "/v1/routine_folders",
            expected_status=200,
            description="Lista pastas/coleções de rotinas",
        )

        # 3. Routines (GET)
        await self.test_endpoint(
            "GET",
            "/v1/routines",
            expected_status=200,
            description="Lista rotinas existentes",
        )

        # 4. User Profile (GET) - Opcional, ajuda a validar auth
        await self.test_endpoint(
            "GET",
            "/v1/user/info",
            expected_status=200,
            description="Valida autenticação e obtém dados do usuário (opcional)",
        )

        print("\n" + "=" * 70)
        print("RESUMO DOS RESULTADOS")
        print("=" * 70)

        self._print_resumo()

    def _print_resumo(self):
        """Imprime resumo dos testes"""
        total = len(self.results)
        sucessos = sum(1 for r in self.results if r.success)
        falhas = total - sucessos

        print(f"Total de testes: {total}")
        print(f"Sucessos: {sucessos} ✅")
        print(f"Falhas: {falhas} ❌")

        if falhas > 0:
            print("\n⚠️  Endpoints com falha:")
            for result in self.results:
                if not result.success:
                    print(
                        f"  - {result.method} {result.endpoint}: {result.status_code} - {result.error}"
                    )

        if sucessos == total:
            print("\n✅ Todos os testes passaram!")

    def salvar_resultados(self, output_dir: str = "docs/flows"):
        """Salva resultados em JSON para documentação"""
        project_root = Path(__file__).resolve().parents[2]
        output_path = project_root / output_dir / "hevy-api-prova-01.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Convertendo resultados para dicts
        resultados_dict = [asdict(r) for r in self.results]

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "timestamp": datetime.utcnow().isoformat(),
                    "base_url": self.base_url,
                    "total_tests": len(self.results),
                    "successful": sum(1 for r in self.results if r.success),
                    "results": resultados_dict,
                },
                f,
                indent=2,
                ensure_ascii=False,
            )

        print(f"\n✅ Resultados salvos em: {output_path}")

        # Também salva um resumo em TXT
        txt_path = output_path.with_suffix(".txt")
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write("PROVA DE CONCEITO — API HEVY\n")
            f.write("=" * 70 + "\n\n")

            for result in self.results:
                f.write(f"Endpoint: {result.method} {result.endpoint}\n")
                f.write(f"Status: {result.status_code} {'✅' if result.success else '❌'}\n")
                if result.item_count > 0:
                    f.write(f"Items: {result.item_count}\n")
                if result.error:
                    f.write(f"Erro: {result.error}\n")
                if result.headers:
                    f.write(f"Headers: {result.headers}\n")
                if result.sample_item:
                    f.write(f"Amostra:\n{json.dumps(result.sample_item, indent=2, ensure_ascii=False)[:500]}...\n")
                f.write("\n" + "-" * 70 + "\n\n")

        print(f"✅ Resumo TXT salvo em: {txt_path}")


async def main():
    """Função principal"""

    if not API_KEY:
        print("❌ ERRO: HEVY_API_KEY não está configurada no .env")
        print("   Instruções:")
        print("   1. Obter API key em https://hevy.com/settings?developer")
        print("   2. Preencher .env com: HEVY_API_KEY=sua_chave")
        sys.exit(1)

    async with HevyApiProver() as prover:
        await prover.run_prova_completa()
        prover.salvar_resultados()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⚠️  Interrompido pelo usuário")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Erro fatal: {e}")
        sys.exit(1)
