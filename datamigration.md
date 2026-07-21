# Data Migrations
## Migration 21/07/2026
- Creation of Affiliation and Sources tables
- Removal of Helga_id from Runner, migration to Sources
- Removal of Fede, Club, migration to Affiliation
````sql
INSERT INTO elo_source (ext_runner_id, source_type, runner_id)
SELECT elo_runner.HELGA_ID, 1, elo_runner.id FROM elo_runner WHERE helga_id is not null;

INSERT INTO elo_affiliation (fede, club, country, runner_id)
SELECT elo_runner.fede, elo_runner.club, 'BEL', elo_runner.id FROM elo_runner WHERE abso = 1;

UPDATE elo_result  SET source_id = elo_source.id FROM elo_source
    WHERE elo_result.runner_id = elo_source.runner_id;
````
