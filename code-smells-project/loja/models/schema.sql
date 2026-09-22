CREATE TABLE usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL CHECK(length(trim(nome)) BETWEEN 2 AND 200),
    email TEXT NOT NULL COLLATE NOCASE UNIQUE,
    senha_hash TEXT NOT NULL,
    tipo TEXT NOT NULL DEFAULT 'cliente' CHECK(tipo IN ('cliente', 'admin')),
    criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE produtos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL CHECK(length(trim(nome)) BETWEEN 2 AND 200),
    descricao TEXT NOT NULL DEFAULT '',
    preco REAL NOT NULL CHECK(preco >= 0 AND preco <= 1000000000),
    estoque INTEGER NOT NULL CHECK(typeof(estoque) = 'integer' AND estoque >= 0),
    categoria TEXT NOT NULL CHECK(categoria IN ('informatica','moveis','vestuario','geral','eletronicos','livros')),
    ativo INTEGER NOT NULL DEFAULT 1 CHECK(ativo IN (0,1)),
    criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE pedidos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE RESTRICT,
    status TEXT NOT NULL DEFAULT 'pendente' CHECK(status IN ('pendente','aprovado','enviado','entregue','cancelado')),
    total REAL NOT NULL CHECK(total >= 0),
    criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE itens_pedido (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pedido_id INTEGER NOT NULL REFERENCES pedidos(id) ON DELETE CASCADE,
    produto_id INTEGER NOT NULL REFERENCES produtos(id) ON DELETE RESTRICT,
    quantidade INTEGER NOT NULL CHECK(typeof(quantidade) = 'integer' AND quantidade > 0),
    preco_unitario REAL NOT NULL CHECK(preco_unitario >= 0)
);
CREATE INDEX pedidos_usuario_idx ON pedidos(usuario_id, id);
CREATE INDEX itens_pedido_idx ON itens_pedido(pedido_id, id);
CREATE INDEX itens_produto_idx ON itens_pedido(produto_id);
PRAGMA user_version = 1;
