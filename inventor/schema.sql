-- MAIN TABLES

CREATE TABLE IF NOT EXISTS activity_log(
        id SERIAL PRIMARY KEY,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        created_by TEXT,
        entity_name TEXT,
        entity_id INTEGER,
        operation TEXT);


CREATE TABLE IF NOT EXISTS item(
        id SERIAL PRIMARY KEY,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        name VARCHAR,
        part_numbers TEXT,
        location VARCHAR,
        sale_price NUMERIC DEFAULT 0,
        quantity NUMERIC DEFAULT 1,
        unit VARCHAR DEFAULT 'pcs',
        condition TEXT,
        info TEXT,
        picture_path TEXT);

CREATE TABLE IF NOT EXISTS item_label(
        id SERIAL PRIMARY KEY,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        label TEXT,
        entity_id INTEGER REFERENCES item(id) ON DELETE CASCADE,
        UNIQUE(entity_id, label));


CREATE OR REPLACE FUNCTION prevent_duplicates_item_label()
RETURNS TRIGGER AS $$
BEGIN
    IF EXISTS (SELECT 1 FROM item_label 
    WHERE label=NEW.label AND entity_id=NEW.entity_id) THEN 
        DELETE FROM item_label 
            WHERE label = NEW.label AND entity_id = NEW.entity_id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;


DROP TRIGGER IF EXISTS prevent_duplicates_trigger ON item_label;
CREATE TRIGGER prevent_duplicates_trigger
BEFORE INSERT ON item_label
FOR EACH ROW 
EXECUTE PROCEDURE prevent_duplicates_item_label();



-- table holding read only columns of entities
-- can be either universal (table_name == NULL) or with a specified table name
CREATE TABLE IF NOT EXISTS read_only(
        id SERIAL PRIMARY KEY,
        table_name VARCHAR,
        column_name VARCHAR,
        UNIQUE(table_name, column_name));


-- TRIGGERS AND FUNCTIONS

--do this on any crud operation on any entity 
CREATE OR REPLACE FUNCTION update_activity_log()
RETURNS TRIGGER AS $$
DECLARE entid INTEGER;
BEGIN
    IF TG_OP = 'DELETE' THEN
        entid := OLD.id;
    ELSE
        entid := NEW.id;
    END IF;
    INSERT INTO activity_log(created_by, entity_name, entity_id, operation) 
        VALUES (SESSION_USER, --TODO: This will not work with SET ROLE, use tundi_session method
            TG_TABLE_NAME, entid, TG_OP);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS update_activity_log_trigger ON item;
CREATE TRIGGER update_activity_log_trigger
AFTER INSERT OR UPDATE OR DELETE ON item 
FOR EACH ROW EXECUTE 
PROCEDURE update_activity_log();

DROP TRIGGER IF EXISTS update_activity_log_trigger ON item_label;
CREATE TRIGGER update_activity_log_trigger
AFTER INSERT OR UPDATE OR DELETE ON item_label
FOR EACH ROW EXECUTE 
PROCEDURE update_activity_log();

--triggers to update mtimes 
CREATE OR REPLACE FUNCTION update_mtime()
RETURNS TRIGGER AS $$
BEGIN
    NEW.modified_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS update_mtime_trigger ON item;
CREATE TRIGGER update_mtime_trigger
BEFORE UPDATE ON item
FOR EACH ROW EXECUTE
PROCEDURE update_mtime();

DROP TRIGGER IF EXISTS update_mtime_trigger ON item_label;
CREATE TRIGGER update_mtime_trigger
BEFORE UPDATE ON item_label
FOR EACH ROW EXECUTE
PROCEDURE update_mtime();

DROP TRIGGER IF EXISTS update_mtime_trigger ON activity_log;
CREATE TRIGGER update_mtime_trigger
BEFORE UPDATE ON activity_log
FOR EACH ROW EXECUTE
PROCEDURE update_mtime();
