# ground_truth_cases.py
# Casos de teste expandidos para benchmark de embeddings
# Cobertura de múltiplas categorias NCM

TEST_CASES = [
    # ==========================================
    # ALIMENTOS E BEBIDAS (Capítulos 01-24)
    # ==========================================

    # Cafés e chás
    ("cafe torrado em graos", "0901"),
    ("cafe solúvel instantâneo", "2101"),
    ("cha preto folhas", "0902"),

    # Grãos e sementes
    ("soja em graos para plantio", "1201"),
    ("milho em graos", "1005"),
    ("feijao preto", "0713"),
    ("arroz em graos descascado", "1006"),
    ("trigo em graos", "1001"),

    # Óleos vegetais
    ("óleo de soja refinado", "1507"),
    ("óleo de girassol", "1512"),
    ("azeite de oliva extra virgem", "1509"),

    # Carnes e derivados
    ("carne bovina congelada", "0202"),
    ("carne bovina fresca refrigerada", "0201"),
    ("carne de frango fresca", "0207"),
    ("carne suína congelada", "0203"),
    ("linguiça defumada", "1601"),

    # Laticínios
    ("leite em pó integral", "0402"),
    ("queijo mussarela", "0406"),
    ("manteiga com sal", "0405"),
    ("iogurte natural", "0403"),

    # Farinhas e massas
    ("farinha de trigo", "1101"),
    ("macarrão espaguete seco", "1902"),

    # Açúcares e doces
    ("açucar cristal", "1701"),
    ("mel de abelhas natural", "0409"),
    ("chocolate em barra ao leite", "1806"),

    # Bebidas
    ("cerveja em lata", "2203"),
    ("vinho tinto seco", "2204"),
    ("suco de laranja natural", "2009"),

    # ==========================================
    # ELETRÔNICOS (Capítulo 85)
    # ==========================================

    ("telefone celular smartphone", "8517"),
    ("carregador usb para celular", "8504"),
    ("fone de ouvido bluetooth", "8518"),
    ("monitor LCD para computador", "8528"),
    ("televisão LED 50 polegadas", "8528"),
    ("cabo HDMI 2 metros", "8544"),
    ("bateria de lítio recarregável", "8506"),
    ("microfone condensador", "8518"),

    # ==========================================
    # INFORMÁTICA (Capítulo 84)
    # ==========================================

    ("notebook computador portátil", "8471"),
    ("computador desktop", "8471"),
    ("impressora laser preto branco", "8443"),
    ("teclado mecânico USB", "8471"),
    ("mouse óptico sem fio", "8471"),
    ("HD externo 1TB USB", "8471"),
    ("webcam full HD", "8525"),

    # ==========================================
    # VEÍCULOS E AUTOPEÇAS (Capítulos 87-89)
    # ==========================================

    ("automóvel sedan gasolina", "8703"),
    ("motocicleta 150cc", "8711"),
    ("pneu radial aro 15", "4011"),
    ("bateria automotiva 60 amperes", "8507"),
    ("filtro de óleo motor", "8421"),
    ("para-choque dianteiro", "8708"),

    # ==========================================
    # VESTUÁRIO E CALÇADOS (Capítulos 61-64)
    # ==========================================

    ("camiseta algodão manga curta", "6109"),
    ("camisa social masculina", "6205"),
    ("calça jeans feminina", "6203"),
    ("vestido feminino casual", "6204"),
    ("sapato couro social masculino", "6403"),
    ("tênis esportivo corrida", "6404"),
    ("sandália feminina couro", "6402"),
    ("meia masculina algodão", "6115"),

    # ==========================================
    # MEDICAMENTOS (Capítulo 30)
    # ==========================================

    ("antibiótico amoxicilina comprimido", "3004"),
    ("analgésico paracetamol", "3004"),
    ("anti-inflamatório ibuprofeno", "3004"),
    ("vitamina C comprimido", "3004"),

    # ==========================================
    # COSMÉTICOS E HIGIENE (Capítulo 33)
    # ==========================================

    ("shampoo para cabelos secos", "3305"),
    ("condicionador capilar", "3305"),
    ("sabonete líquido antibacteriano", "3401"),
    ("creme dental com flúor", "3306"),
    ("perfume fragrância importada", "3303"),
    ("desodorante antitranspirante", "3307"),

    # ==========================================
    # MATERIAIS DE CONSTRUÇÃO
    # ==========================================

    ("cimento portland saco 50kg", "2523"),
    ("tijolo cerâmico furado", "6904"),
    ("tinta látex acrílica branca", "3209"),
    ("piso cerâmico porcelanato", "6907"),
    ("porta de madeira maciça", "4418"),
    ("janela alumínio vidro", "7610"),

    # ==========================================
    # MÓVEIS (Capítulo 94)
    # ==========================================

    ("mesa de jantar madeira", "9403"),
    ("cadeira escritório giratória", "9401"),
    ("sofá 3 lugares tecido", "9401"),
    ("cama casal box molas", "9403"),
    ("guarda-roupa 6 portas", "9403"),

    # ==========================================
    # LIVROS E PAPEL (Capítulos 48-49)
    # ==========================================

    ("livro impresso capa dura", "4901"),
    ("caderno universitário 200 folhas", "4820"),
    ("papel sulfite A4 resma", "4802"),

    # ==========================================
    # BRINQUEDOS (Capítulo 95)
    # ==========================================

    ("boneca plástico articulada", "9503"),
    ("carrinho controle remoto", "9503"),
    ("bola futebol couro sintético", "9506"),

    # ==========================================
    # FERRAMENTAS (Capítulo 82)
    # ==========================================

    ("martelo cabo madeira", "8205"),
    ("chave de fenda jogo", "8205"),
    ("furadeira elétrica portátil", "8467"),
    ("serra circular elétrica", "8467"),
]


# Casos especiais para testar edge cases
EDGE_CASES = [
    # Consultas muito genéricas
    ("carro", "8703"),
    ("celular", "8517"),
    ("comida", "2106"),  # Preparações alimentícias

    # Consultas muito específicas
    ("smartphone samsung galaxy s21 128gb preto", "8517"),
    ("notebook dell inspiron 15 core i7 16gb", "8471"),

    # Consultas com erros de digitação
    ("cafe torrado graos", "0901"),  # sem "em"
    ("telefon celular", "8517"),  # erro ortográfico

    # Consultas em inglês
    ("coffee beans roasted", "0901"),
    ("mobile phone", "8517"),

    # Consultas técnicas
    ("NCM 8517", "8517"),
    ("capitulo 09", "09"),  # Café e especiarias
]


# Casos para testar atributos
ATTRIBUTE_TEST_CASES = [
    # NCMs que devem ter atributos
    ("leite em pó", "0402", True),
    ("telefone celular", "8517", True),
    ("medicamento genérico", "3004", True),

    # NCMs sem atributos específicos
    ("pedra natural", "2516", False),
]


def get_all_test_cases():
    """Retorna todos os casos de teste"""
    return TEST_CASES


def get_edge_cases():
    """Retorna apenas edge cases"""
    return EDGE_CASES


def get_test_cases_by_chapter(chapter):
    """Retorna casos de teste de um capítulo específico"""
    return [
        (query, ncm) for query, ncm in TEST_CASES
        if ncm.startswith(chapter)
    ]


def get_category_distribution():
    """Retorna distribuição de casos por categoria"""
    distribution = {}
    for query, ncm in TEST_CASES:
        chapter = ncm[:2]
        distribution[chapter] = distribution.get(chapter, 0) + 1
    return distribution


if __name__ == "__main__":
    print(f"Total de casos de teste: {len(TEST_CASES)}")
    print(f"Edge cases: {len(EDGE_CASES)}")
    print(f"Casos de atributos: {len(ATTRIBUTE_TEST_CASES)}")
    print(f"\nDistribuição por capítulo:")
    for chapter, count in sorted(get_category_distribution().items()):
        print(f"  Capítulo {chapter}: {count} casos")
