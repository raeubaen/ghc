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

ALTER TABLE ONLY public.payloads DROP CONSTRAINT payloads_tagid_fkey;
ALTER TABLE ONLY public.payloads DROP CONSTRAINT payloads_fieldid_fkey;
DROP INDEX public.payloads_field_tag;
DROP INDEX public.p_tagid;
DROP INDEX public.p_iov;
DROP INDEX public.ecs_dbid_iov_tag;
ALTER TABLE ONLY public.tags DROP CONSTRAINT tags_pkey;
ALTER TABLE ONLY public.payloads DROP CONSTRAINT payloads_pkey;
ALTER TABLE ONLY public.fields DROP CONSTRAINT fields_pkey;
ALTER TABLE public.tags ALTER COLUMN tagid DROP DEFAULT;
ALTER TABLE public.fields ALTER COLUMN fieldid DROP DEFAULT;
DROP SEQUENCE public.tags_tagid_seq;
DROP MATERIALIZED VIEW public.iovs;
DROP SEQUENCE public.fields_fieldid_seq;
DROP TABLE public.fields;
DROP MATERIALIZED VIEW public.ecalchannelstatus;
DROP TABLE public.tags;
DROP TABLE public.payloads;
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
-- Name: payloads; Type: TABLE; Schema: public; Owner: apache
--

CREATE TABLE payloads (
    iov integer NOT NULL,
    tagid integer NOT NULL,
    fieldid integer NOT NULL,
    value real NOT NULL,
    dbid integer NOT NULL
);


ALTER TABLE payloads OWNER TO apache;

--
-- Name: tags; Type: TABLE; Schema: public; Owner: apache
--

CREATE TABLE tags (
    tagid integer NOT NULL,
    tag character varying(50)
);


ALTER TABLE tags OWNER TO apache;

--
-- Name: ecalchannelstatus; Type: MATERIALIZED VIEW; Schema: public; Owner: apache
--

CREATE MATERIALIZED VIEW ecalchannelstatus AS
 SELECT payloads.iov,
    payloads.dbid,
    payloads.value AS status,
    tags.tag
   FROM (payloads
     JOIN tags ON ((payloads.tagid = tags.tagid)))
  WHERE ((payloads.fieldid = 11) AND ((tags.tag)::text ~~ 'EcalChannelStatus%'::text) AND (payloads.value <> (0)::double precision))
  WITH NO DATA;


ALTER TABLE ecalchannelstatus OWNER TO apache;

--
-- Name: fields; Type: TABLE; Schema: public; Owner: apache
--

CREATE TABLE fields (
    fieldid integer NOT NULL,
    field character varying(250)
);


ALTER TABLE fields OWNER TO apache;

--
-- Name: fields_fieldid_seq; Type: SEQUENCE; Schema: public; Owner: apache
--

CREATE SEQUENCE fields_fieldid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE fields_fieldid_seq OWNER TO apache;

--
-- Name: fields_fieldid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: apache
--

ALTER SEQUENCE fields_fieldid_seq OWNED BY fields.fieldid;


--
-- Name: iovs; Type: MATERIALIZED VIEW; Schema: public; Owner: apache
--

CREATE MATERIALIZED VIEW iovs AS
 SELECT payloads.iov,
    payloads.fieldid,
    payloads.tagid
   FROM payloads
  GROUP BY payloads.iov, payloads.fieldid, payloads.tagid
  WITH NO DATA;


ALTER TABLE iovs OWNER TO apache;

--
-- Name: tags_tagid_seq; Type: SEQUENCE; Schema: public; Owner: apache
--

CREATE SEQUENCE tags_tagid_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE tags_tagid_seq OWNER TO apache;

--
-- Name: tags_tagid_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: apache
--

ALTER SEQUENCE tags_tagid_seq OWNED BY tags.tagid;


--
-- Name: fieldid; Type: DEFAULT; Schema: public; Owner: apache
--

ALTER TABLE ONLY fields ALTER COLUMN fieldid SET DEFAULT nextval('fields_fieldid_seq'::regclass);


--
-- Name: tagid; Type: DEFAULT; Schema: public; Owner: apache
--

ALTER TABLE ONLY tags ALTER COLUMN tagid SET DEFAULT nextval('tags_tagid_seq'::regclass);


--
-- Name: fields_pkey; Type: CONSTRAINT; Schema: public; Owner: apache
--

ALTER TABLE ONLY fields
    ADD CONSTRAINT fields_pkey PRIMARY KEY (fieldid);


--
-- Name: payloads_pkey; Type: CONSTRAINT; Schema: public; Owner: apache
--

ALTER TABLE ONLY payloads
    ADD CONSTRAINT payloads_pkey PRIMARY KEY (iov, tagid, fieldid, dbid);


--
-- Name: tags_pkey; Type: CONSTRAINT; Schema: public; Owner: apache
--

ALTER TABLE ONLY tags
    ADD CONSTRAINT tags_pkey PRIMARY KEY (tagid);


--
-- Name: ecs_dbid_iov_tag; Type: INDEX; Schema: public; Owner: apache
--

CREATE INDEX ecs_dbid_iov_tag ON ecalchannelstatus USING btree (dbid, iov, tag);


--
-- Name: p_iov; Type: INDEX; Schema: public; Owner: apache
--

CREATE INDEX p_iov ON payloads USING btree (iov);


--
-- Name: p_tagid; Type: INDEX; Schema: public; Owner: apache
--

CREATE INDEX p_tagid ON payloads USING btree (tagid);


--
-- Name: payloads_field_tag; Type: INDEX; Schema: public; Owner: apache
--

CREATE INDEX payloads_field_tag ON payloads USING btree (tagid, fieldid) WHERE ((tagid = 6) AND (fieldid = 11));


--
-- Name: payloads_fieldid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: apache
--

ALTER TABLE ONLY payloads
    ADD CONSTRAINT payloads_fieldid_fkey FOREIGN KEY (fieldid) REFERENCES fields(fieldid);


--
-- Name: payloads_tagid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: apache
--

ALTER TABLE ONLY payloads
    ADD CONSTRAINT payloads_tagid_fkey FOREIGN KEY (tagid) REFERENCES tags(tagid);


--
-- Name: public; Type: ACL; Schema: -; Owner: postgres
--

REVOKE ALL ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON SCHEMA public FROM postgres;
GRANT ALL ON SCHEMA public TO postgres;
GRANT ALL ON SCHEMA public TO PUBLIC;


--
-- Name: payloads; Type: ACL; Schema: public; Owner: apache
--

REVOKE ALL ON TABLE payloads FROM PUBLIC;
REVOKE ALL ON TABLE payloads FROM apache;
GRANT ALL ON TABLE payloads TO apache;
GRANT SELECT ON TABLE payloads TO pfgreadonly;


--
-- Name: tags; Type: ACL; Schema: public; Owner: apache
--

REVOKE ALL ON TABLE tags FROM PUBLIC;
REVOKE ALL ON TABLE tags FROM apache;
GRANT ALL ON TABLE tags TO apache;
GRANT SELECT ON TABLE tags TO pfgreadonly;


--
-- Name: ecalchannelstatus; Type: ACL; Schema: public; Owner: apache
--

REVOKE ALL ON TABLE ecalchannelstatus FROM PUBLIC;
REVOKE ALL ON TABLE ecalchannelstatus FROM apache;
GRANT ALL ON TABLE ecalchannelstatus TO apache;
GRANT SELECT ON TABLE ecalchannelstatus TO pfgreadonly;


--
-- Name: fields; Type: ACL; Schema: public; Owner: apache
--

REVOKE ALL ON TABLE fields FROM PUBLIC;
REVOKE ALL ON TABLE fields FROM apache;
GRANT ALL ON TABLE fields TO apache;
GRANT SELECT ON TABLE fields TO pfgreadonly;


--
-- Name: iovs; Type: ACL; Schema: public; Owner: apache
--

REVOKE ALL ON TABLE iovs FROM PUBLIC;
REVOKE ALL ON TABLE iovs FROM apache;
GRANT ALL ON TABLE iovs TO apache;
GRANT SELECT ON TABLE iovs TO pfgreadonly;


--
-- PostgreSQL database dump complete
--

