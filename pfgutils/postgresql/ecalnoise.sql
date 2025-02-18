--
-- PostgreSQL database dump
--

-- Dumped from database version 9.5.3
-- Dumped by pg_dump version 9.5.3

SET statement_timeout = 0;
SET lock_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SET check_function_bodies = false;
SET client_min_messages = warning;
SET row_security = off;

SET search_path = public, pg_catalog;

ALTER TABLE ONLY public.rms DROP CONSTRAINT rms_datasetid_fkey;
DROP INDEX public.rpm_value_lowrg12;
DROP INDEX public.rms_run;
DROP INDEX public.rms_lrg12;
DROP INDEX public.rms_datasetid;
DROP INDEX public.laser3_run;
DROP INDEX public.dbid;
DROP INDEX public.datasets_dataset;
ALTER TABLE ONLY public.rms DROP CONSTRAINT rms_pkey;
ALTER TABLE ONLY public.laser3 DROP CONSTRAINT laser3_pkey;
ALTER TABLE ONLY public.datasets DROP CONSTRAINT datasets_pkey;
ALTER TABLE public.datasets ALTER COLUMN id DROP DEFAULT;
DROP TABLE public.rms;
DROP TABLE public.laser3;
DROP SEQUENCE public.datasets_id_seq;
DROP TABLE public.datasets;
DROP EXTENSION plpgsql;
DROP SCHEMA public;
--
-- Name: public; Type: SCHEMA; Schema: -; Owner: postgres
--

CREATE SCHEMA public;


ALTER SCHEMA public OWNER TO postgres;

--
-- Name: SCHEMA public; Type: COMMENT; Schema: -; Owner: postgres
--

COMMENT ON SCHEMA public IS 'standard public schema';


--
-- Name: plpgsql; Type: EXTENSION; Schema: -; Owner: 
--

CREATE EXTENSION IF NOT EXISTS plpgsql WITH SCHEMA pg_catalog;


--
-- Name: EXTENSION plpgsql; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION plpgsql IS 'PL/pgSQL procedural language';


SET search_path = public, pg_catalog;

SET default_tablespace = '';

SET default_with_oids = false;

--
-- Name: datasets; Type: TABLE; Schema: public; Owner: apache
--

CREATE TABLE datasets (
    id integer NOT NULL,
    dataset character varying(255) NOT NULL
);


ALTER TABLE datasets OWNER TO apache;

--
-- Name: datasets_id_seq; Type: SEQUENCE; Schema: public; Owner: apache
--

CREATE SEQUENCE datasets_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE datasets_id_seq OWNER TO apache;

--
-- Name: datasets_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: apache
--

ALTER SEQUENCE datasets_id_seq OWNED BY datasets.id;


--
-- Name: laser3; Type: TABLE; Schema: public; Owner: apache
--

CREATE TABLE laser3 (
    dbid integer NOT NULL,
    run integer NOT NULL,
    value real NOT NULL
);


ALTER TABLE laser3 OWNER TO apache;

--
-- Name: rms; Type: TABLE; Schema: public; Owner: apache
--

CREATE TABLE rms (
    dbid integer NOT NULL,
    run integer NOT NULL,
    rms real,
    datasetid integer NOT NULL,
    mean real
);


ALTER TABLE rms OWNER TO apache;

--
-- Name: id; Type: DEFAULT; Schema: public; Owner: apache
--

ALTER TABLE ONLY datasets ALTER COLUMN id SET DEFAULT nextval('datasets_id_seq'::regclass);


--
-- Name: datasets_pkey; Type: CONSTRAINT; Schema: public; Owner: apache
--

ALTER TABLE ONLY datasets
    ADD CONSTRAINT datasets_pkey PRIMARY KEY (id);


--
-- Name: laser3_pkey; Type: CONSTRAINT; Schema: public; Owner: apache
--

ALTER TABLE ONLY laser3
    ADD CONSTRAINT laser3_pkey PRIMARY KEY (dbid, run);


--
-- Name: rms_pkey; Type: CONSTRAINT; Schema: public; Owner: apache
--

ALTER TABLE ONLY rms
    ADD CONSTRAINT rms_pkey PRIMARY KEY (dbid, run, datasetid);


--
-- Name: datasets_dataset; Type: INDEX; Schema: public; Owner: apache
--

CREATE INDEX datasets_dataset ON datasets USING btree (dataset);


--
-- Name: dbid; Type: INDEX; Schema: public; Owner: apache
--

CREATE INDEX dbid ON laser3 USING btree (dbid);


--
-- Name: laser3_run; Type: INDEX; Schema: public; Owner: apache
--

CREATE INDEX laser3_run ON laser3 USING btree (run);


--
-- Name: rms_datasetid; Type: INDEX; Schema: public; Owner: apache
--

CREATE INDEX rms_datasetid ON rms USING btree (datasetid);


--
-- Name: rms_lrg12; Type: INDEX; Schema: public; Owner: apache
--

CREATE INDEX rms_lrg12 ON rms USING btree (rms) WHERE ((rms)::numeric >= 2.1);


--
-- Name: rms_run; Type: INDEX; Schema: public; Owner: apache
--

CREATE INDEX rms_run ON rms USING btree (run);


--
-- Name: rpm_value_lowrg12; Type: INDEX; Schema: public; Owner: apache
--

CREATE INDEX rpm_value_lowrg12 ON rms USING btree (rms) WHERE (((rms)::numeric < 0.4) AND ((rms)::numeric > (0)::numeric));


--
-- Name: rms_datasetid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: apache
--

ALTER TABLE ONLY rms
    ADD CONSTRAINT rms_datasetid_fkey FOREIGN KEY (datasetid) REFERENCES datasets(id);


--
-- Name: public; Type: ACL; Schema: -; Owner: postgres
--

REVOKE ALL ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON SCHEMA public FROM postgres;
GRANT ALL ON SCHEMA public TO postgres;
GRANT ALL ON SCHEMA public TO PUBLIC;


--
-- Name: datasets; Type: ACL; Schema: public; Owner: apache
--

REVOKE ALL ON TABLE datasets FROM PUBLIC;
REVOKE ALL ON TABLE datasets FROM apache;
GRANT ALL ON TABLE datasets TO apache;
GRANT SELECT ON TABLE datasets TO pfgreadonly;


--
-- Name: datasets_id_seq; Type: ACL; Schema: public; Owner: apache
--

REVOKE ALL ON SEQUENCE datasets_id_seq FROM PUBLIC;
REVOKE ALL ON SEQUENCE datasets_id_seq FROM apache;
GRANT ALL ON SEQUENCE datasets_id_seq TO apache;
GRANT SELECT ON SEQUENCE datasets_id_seq TO pfgreadonly;


--
-- Name: laser3; Type: ACL; Schema: public; Owner: apache
--

REVOKE ALL ON TABLE laser3 FROM PUBLIC;
REVOKE ALL ON TABLE laser3 FROM apache;
GRANT ALL ON TABLE laser3 TO apache;
GRANT SELECT ON TABLE laser3 TO pfgreadonly;


--
-- Name: rms; Type: ACL; Schema: public; Owner: apache
--

REVOKE ALL ON TABLE rms FROM PUBLIC;
REVOKE ALL ON TABLE rms FROM apache;
GRANT ALL ON TABLE rms TO apache;
GRANT SELECT ON TABLE rms TO pfgreadonly;


--
-- PostgreSQL database dump complete
--

