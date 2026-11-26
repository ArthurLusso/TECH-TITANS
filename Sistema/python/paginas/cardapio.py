
import streamlit as st
import uuid

from pathlib import Path

from data_base.cardapio import (
    listar_pratos,
    listar_categorias,
    cadastrar_prato,
    editar_prato,
    alterar_disponibilidade,
    remover_imagem_prato,
    excluir_prato
)

from data_base.receitas import (
    listar_variacoes_estoque,
    listar_receita,
    salvar_item_receita,
    remover_item_receita,
    unidades_compativeis
)


BASE_DIR = Path(__file__).resolve().parent.parent
PASTA_PRATOS = BASE_DIR / "assets" / "pratos"

PASTA_PRATOS.mkdir(parents=True, exist_ok=True)

TAMANHO_MAXIMO = 5 * 1024 * 1024

FORMATOS_PERMITIDOS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp"
}

CATEGORIAS_PADRAO = [
    "Tacos",
    "Burritos",
    "Quesadillas",
    "Nachos",
    "Bebidas",
    "Sobremesas",
    "Outros"
]


def formatar_preco(valor):
    return (
        f"R$ {valor:,.2f}"
        .replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )


def salvar_imagem(arquivo):
    if arquivo is None:
        return None

    extensao = Path(arquivo.name).suffix.lower()

    if extensao not in FORMATOS_PERMITIDOS:
        raise ValueError(
            "Formato inválido. Utilize JPG, JPEG, PNG ou WEBP."
        )

    conteudo = arquivo.getvalue()

    if not conteudo:
        raise ValueError("O arquivo de imagem está vazio.")

    if len(conteudo) > TAMANHO_MAXIMO:
        raise ValueError("A imagem deve ter no máximo 5 MB.")

    try:
        from PIL import Image
        from io import BytesIO

        with Image.open(BytesIO(conteudo)) as imagem:
            imagem.verify()

    except Exception:
        raise ValueError("O arquivo enviado não é uma imagem válida.")

    nome_arquivo = f"{uuid.uuid4().hex}{extensao}"
    caminho_completo = PASTA_PRATOS / nome_arquivo

    with open(caminho_completo, "wb") as arquivo_destino:
        arquivo_destino.write(conteudo)

    return f"assets/pratos/{nome_arquivo}"


def obter_caminho_imagem(caminho):
    if not caminho:
        return None

    arquivo = (BASE_DIR / caminho).resolve()
    pasta = PASTA_PRATOS.resolve()

    if arquivo.parent != pasta:
        return None

    if arquivo.is_file():
        return str(arquivo)

    return None


def apagar_arquivo_imagem(caminho):
    arquivo = obter_caminho_imagem(caminho)

    if arquivo:
        Path(arquivo).unlink(missing_ok=True)


st.title("🌮 Cardápio")
st.write("Gerencie os pratos, preços e receitas do restaurante.")

try:
    todos_pratos = listar_pratos()
    variacoes_estoque = listar_variacoes_estoque()

except Exception as erro:
    st.error(f"Erro ao carregar o cardápio ou estoque: {erro}")
    st.stop()


total_pratos = len(todos_pratos)

pratos_ativos = sum(
    1 for prato in todos_pratos
    if prato["disponivel"] == 1
)

pratos_inativos = total_pratos - pratos_ativos

col1, col2, col3 = st.columns(3)

col1.metric("Total de pratos", total_pratos)
col2.metric("Disponíveis", pratos_ativos)
col3.metric("Indisponíveis", pratos_inativos)

st.divider()


with st.expander("➕ Cadastrar novo prato", expanded=False):

    with st.form("form_cadastrar_prato", clear_on_submit=True):

        nome = st.text_input(
            "Nome do prato",
            placeholder="Ex.: Taco de Picanha"
        )

        descricao = st.text_area(
            "Descrição",
            placeholder="Descreva os ingredientes e características do prato."
        )

        col1, col2 = st.columns(2)

        with col1:
            categoria = st.selectbox(
                "Categoria",
                CATEGORIAS_PADRAO
            )

        with col2:
            preco = st.number_input(
                "Preço (R$)",
                min_value=0.0,
                value=0.0,
                step=1.0,
                format="%.2f"
            )

        foto = st.file_uploader(
            "Foto do prato",
            type=["jpg", "jpeg", "png", "webp"],
            help="Envie uma imagem de até 5 MB.",
            key="foto_novo_prato"
        )

        cadastrar = st.form_submit_button(
            "Cadastrar prato",
            use_container_width=True
        )

        if cadastrar:

            if not nome.strip():
                st.warning("Informe o nome do prato.")

            elif preco <= 0:
                st.warning("Informe um preço maior que zero.")

            else:
                caminho_foto = None

                try:
                    caminho_foto = salvar_imagem(foto)

                    cadastrar_prato(
                        nome,
                        descricao,
                        categoria,
                        preco,
                        caminho_foto
                    )

                    st.success("Prato cadastrado com sucesso!")
                    st.rerun()

                except Exception as erro:
                    if caminho_foto:
                        apagar_arquivo_imagem(caminho_foto)

                    st.error(f"Não foi possível cadastrar o prato: {erro}")


st.divider()

st.subheader("Pratos cadastrados")

try:
    categorias_banco = listar_categorias()

except Exception as erro:
    st.error(f"Erro ao carregar categorias: {erro}")
    categorias_banco = []

categorias_filtro = ["Todas"] + categorias_banco

col1, col2, col3 = st.columns([2, 1, 1])

with col1:
    busca = st.text_input(
        "Buscar prato",
        placeholder="Digite o nome do prato..."
    )

with col2:
    filtro_categoria = st.selectbox(
        "Categoria",
        categorias_filtro
    )

with col3:
    filtro_disponibilidade = st.selectbox(
        "Disponibilidade",
        ["Todas", "Disponíveis", "Indisponíveis"]
    )


if filtro_disponibilidade == "Disponíveis":
    disponibilidade = True
elif filtro_disponibilidade == "Indisponíveis":
    disponibilidade = False
else:
    disponibilidade = None


try:
    pratos = listar_pratos(
        busca=busca,
        categoria=filtro_categoria,
        disponibilidade=disponibilidade
    )

except Exception as erro:
    st.error(f"Erro ao buscar pratos: {erro}")
    pratos = []


if not pratos:
    st.info("Nenhum prato encontrado com os filtros selecionados.")

else:

    st.caption(f"{len(pratos)} prato(s) encontrado(s).")

    for prato in pratos:

        prato_id = prato["id"]
        nome_prato = prato["nome"]
        descricao_prato = prato["descricao"] or ""
        categoria_prato = prato["categoria"] or "Sem categoria"
        preco_prato = prato["preco"]
        disponivel_prato = prato["disponivel"] == 1
        imagem_prato = prato["imagem"]

        status = (
            "🟢 Disponível"
            if disponivel_prato
            else "🔴 Indisponível"
        )

        col_foto, col_dados = st.columns([1, 3])

        with col_foto:
            caminho_foto = obter_caminho_imagem(imagem_prato)

            if caminho_foto:
                st.image(caminho_foto, width=190)
            else:
                st.markdown("## 🌮")
                st.caption("Sem foto cadastrada")

        with col_dados:
            st.subheader(nome_prato)
            st.write(f"**Categoria:** {categoria_prato}")
            st.write(f"**Preço:** {formatar_preco(preco_prato)}")
            st.write(f"**Disponibilidade:** {status}")

            if descricao_prato:
                st.write(descricao_prato)
            else:
                st.caption("Sem descrição.")

        with st.expander(f"Gerenciar {nome_prato}"):

            st.markdown("#### ✏️ Editar informações")

            with st.form(f"form_editar_{prato_id}"):

                novo_nome = st.text_input(
                    "Nome",
                    value=nome_prato
                )

                nova_descricao = st.text_area(
                    "Descrição",
                    value=descricao_prato
                )

                categorias_edicao = list(
                    dict.fromkeys(
                        CATEGORIAS_PADRAO
                        + categorias_banco
                        + [categoria_prato]
                    )
                )

                indice_categoria = categorias_edicao.index(
                    categoria_prato
                )

                col1, col2 = st.columns(2)

                with col1:
                    nova_categoria = st.selectbox(
                        "Categoria",
                        categorias_edicao,
                        index=indice_categoria
                    )

                with col2:
                    novo_preco = st.number_input(
                        "Preço (R$)",
                        min_value=0.0,
                        value=float(preco_prato),
                        step=1.0,
                        format="%.2f"
                    )

                nova_foto = st.file_uploader(
                    "Trocar foto do prato",
                    type=["jpg", "jpeg", "png", "webp"],
                    help="Deixe vazio para manter a foto atual."
                )

                salvar_edicao = st.form_submit_button(
                    "Salvar alterações",
                    use_container_width=True
                )

                if salvar_edicao:

                    if not novo_nome.strip():
                        st.warning("Informe o nome do prato.")

                    elif novo_preco <= 0:
                        st.warning("Informe um preço maior que zero.")

                    else:
                        nova_imagem = None

                        try:
                            if nova_foto is not None:
                                nova_imagem = salvar_imagem(nova_foto)

                            editar_prato(
                                prato_id,
                                novo_nome,
                                nova_descricao,
                                nova_categoria,
                                novo_preco,
                                nova_imagem
                            )

                            if nova_imagem:
                                apagar_arquivo_imagem(imagem_prato)

                            st.success("Prato atualizado com sucesso!")
                            st.rerun()

                        except Exception as erro:
                            if nova_imagem:
                                apagar_arquivo_imagem(nova_imagem)

                            st.error(f"Erro ao editar prato: {erro}")

            st.divider()

            st.markdown("#### 📷 Foto atual")

            if caminho_foto:

                if st.button(
                    "Remover foto",
                    key=f"remover_foto_{prato_id}"
                ):

                    try:
                        remover_imagem_prato(prato_id)
                        apagar_arquivo_imagem(imagem_prato)

                        st.success("Foto removida com sucesso!")
                        st.rerun()

                    except Exception as erro:
                        st.error(f"Erro ao remover foto: {erro}")

            else:
                st.caption("Este prato ainda não possui uma foto.")

            st.divider()

            st.markdown("#### 🥑 Ficha técnica do prato")

            st.caption(
                "Informe os ingredientes e as quantidades necessários "
                "para preparar uma unidade deste prato."
            )

            try:
                receita = listar_receita(prato_id)

                if receita:

                    for componente in receita:

                        col1, col2 = st.columns([4, 1])

                        with col1:
                            st.write(
                                f"**{componente['ingrediente']} — "
                                f"{componente['variacao']}**"
                            )

                            st.caption(
                                f"Necessário: "
                                f"{componente['quantidade_necessaria']:g} "
                                f"{componente['unidade_receita']} por prato"
                            )

                            st.caption(
                                f"Estoque atual: "
                                f"{componente['estoque_atual']:g} "
                                f"{componente['unidade_estoque']}"
                            )

                        with col2:
                            if st.button(
                                "Remover",
                                key=f"remover_receita_{componente['receita_id']}"
                            ):

                                try:
                                    remover_item_receita(
                                        componente["receita_id"]
                                    )

                                    st.success("Ingrediente removido da receita.")
                                    st.rerun()

                                except Exception as erro:
                                    st.error(str(erro))

                else:
                    st.info(
                        "Este prato ainda não possui ingredientes "
                        "associados ao estoque."
                    )

                if variacoes_estoque:

                    variacoes_por_id = {
                        variacao["id"]: variacao
                        for variacao in variacoes_estoque
                    }

                    with st.form(f"form_receita_{prato_id}"):

                        variacao_id = st.selectbox(
                            "Ingrediente e variação do estoque",
                            options=list(variacoes_por_id.keys()),
                            format_func=lambda id: (
                                f"{variacoes_por_id[id]['ingrediente']} — "
                                f"{variacoes_por_id[id]['variacao']} "
                                f"({variacoes_por_id[id]['quantidade']:g} "
                                f"{variacoes_por_id[id]['unidade']} disponíveis)"
                            )
                        )

                        variacao_selecionada = variacoes_por_id[variacao_id]

                        unidades = unidades_compativeis(
                            variacao_selecionada["unidade"]
                        )

                        unidade_padrao = variacao_selecionada["unidade"]

                        if unidade_padrao == "kg":
                            unidade_padrao = "g"

                        elif unidade_padrao == "L":
                            unidade_padrao = "ml"

                        indice_unidade = unidades.index(
                            unidade_padrao
                        )

                        unidade = st.selectbox(
                            "Unidade utilizada na receita",
                            unidades,
                            index=indice_unidade
                        )

                        quantidade = st.number_input(
                            "Quantidade necessária por prato",
                            min_value=0.001,
                            value=1.0,
                            step=1.0,
                            format="%.3f"
                        )

                        salvar_receita = st.form_submit_button(
                            "Adicionar ingrediente à receita",
                            use_container_width=True
                        )

                        if salvar_receita:

                            try:
                                salvar_item_receita(
                                    prato_id,
                                    variacao_id,
                                    quantidade,
                                    unidade
                                )

                                st.success(
                                    "Ingrediente adicionado à receita!"
                                )

                                st.rerun()

                            except Exception as erro:
                                st.error(
                                    f"Não foi possível salvar a receita: {erro}"
                                )

                else:

                    st.warning(
                        "Cadastre ingredientes e variações na tela Estoque "
                        "antes de montar a ficha técnica."
                    )

            except Exception as erro:
                st.error(f"Erro ao carregar a ficha técnica: {erro}")

            st.divider()

            st.markdown("#### Disponibilidade")

            if disponivel_prato:

                if st.button(
                    "Desativar prato",
                    key=f"desativar_{prato_id}",
                    use_container_width=True
                ):

                    try:
                        alterar_disponibilidade(prato_id, False)
                        st.success("Prato desativado!")
                        st.rerun()

                    except Exception as erro:
                        st.error(f"Erro ao alterar disponibilidade: {erro}")

            else:

                if st.button(
                    "Ativar prato",
                    key=f"ativar_{prato_id}",
                    use_container_width=True
                ):

                    try:
                        alterar_disponibilidade(prato_id, True)
                        st.success("Prato ativado!")
                        st.rerun()

                    except Exception as erro:
                        st.error(f"Erro ao alterar disponibilidade: {erro}")

            st.divider()

            st.markdown("#### 🗑️ Excluir prato")

            confirmar = st.checkbox(
                "Confirmo que desejo excluir este prato.",
                key=f"confirmar_exclusao_{prato_id}"
            )

            if st.button(
                "Excluir prato",
                key=f"excluir_{prato_id}",
                disabled=not confirmar,
                use_container_width=True
            ):

                try:
                    excluir_prato(prato_id)
                    apagar_arquivo_imagem(imagem_prato)

                    st.success("Prato excluído com sucesso!")
                    st.rerun()

                except Exception as erro:
                    st.error(
                        "Não foi possível excluir o prato. "
                        "Verifique se ele já foi utilizado em pedidos "
                        "ou se possui registros vinculados. "
                        f"Detalhes: {erro}"
                    )

        st.divider()
