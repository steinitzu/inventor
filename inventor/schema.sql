CREATE TABLE items(
        id SERIAL PRIMARY KEY,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        name VARCHAR,
        part_numbers TEXT,
        location VARCHAR,
        sale_price NUMERIC,
        quantity NUMERIC,
        unit VARCHAR DEFAULT 'pcs',
        condition TEXT,
        info TEXT,
        picture_path TEXT);

CREATE TABLE item_labels(
        id SERIAL PRIMARY KEY,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        label TEXT,
        entity_id INTEGER REFERENCES items(id) ON DELETE CASCADE,
        UNIQUE(entity_id, label));

CREATE OR REPLACE FUNCTION update_mtime()
RETURNS TRIGGER AS $$
BEGIN
    NEW.modified_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_mtime_trigger
BEFORE UPDATE ON items
FOR EACH ROW EXECUTE
PROCEDURE update_mtime();




