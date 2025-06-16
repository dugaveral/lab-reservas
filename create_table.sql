CREATE TABLE IF NOT EXISTS reservas (
    id SERIAL PRIMARY KEY,
    equipo TEXT NOT NULL,
    inicio TIMESTAMP NOT NULL,
    fin TIMESTAMP NOT NULL,
    usuario TEXT NOT NULL,
    codigo TEXT
);
