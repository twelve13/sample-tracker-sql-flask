DROP TABLE IF EXISTS user;
DROP TABLE IF EXISTS post;
DROP TABLE IF EXISTS sample;
DROP TABLE IF EXISTS extraction;

CREATE TABLE user (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT UNIQUE NOT NULL,
  password TEXT NOT NULL
);


CREATE TABLE extraction (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  extractionName TEXT UNIQUE NOT NULL,
  goalDate TEXT,
  analyst TEXT,
  notes TEXT,
  bbpAdded INTEGER,
  extracted INTEGER
);

CREATE TABLE sample (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  sampleName TEXT UNIQUE NOT NULL,
  extraction_id INTEGER,
  extraction_name TEXT,
  notes TEXT,
  strs INTEGER,
  mito INTEGER,
  isPriority INTEGER,
  analyst TEXT,
  cleaned INTEGER NOT NULL,
  sampled INTEGER NOT NULL,
  FOREIGN KEY (extraction_id) REFERENCES extraction (id)
);

CREATE TABLE archive (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  sampleName TEXT UNIQUE NOT NULL,
  extraction_id INTEGER,
  extraction_name TEXT,
  notes TEXT,
  strs INTEGER,
  mito INTEGER,
  analyst TEXT,
  FOREIGN KEY (extraction_id) REFERENCES extraction (id)
);

