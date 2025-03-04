--
-- PostgreSQL database dump
--

BEGIN;

ALTER TABLE ONLY public."values" DROP CONSTRAINT values_keyid_fkey;
ALTER TABLE ONLY public."values" DROP CONSTRAINT values_pkey;
ALTER TABLE ONLY public.valuekeys DROP CONSTRAINT valuekeys_pkey;
ALTER TABLE ONLY public.runs DROP CONSTRAINT runs_pkey;
ALTER TABLE ONLY public.flags DROP CONSTRAINT flags_pkey;
ALTER TABLE ONLY public.badchannels DROP CONSTRAINT badchannel_pkey;
DROP TABLE public."values";
DROP TABLE public.valuekeys;
DROP TABLE public.runs;
DROP TABLE public.flags;
DROP TABLE public.badchannels;
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
-- Name: badchannels; Type: TABLE; Schema: public; Owner: apache; Tablespace: 
--

CREATE TABLE badchannels (
    dbid integer NOT NULL,
    comment text NOT NULL
);


ALTER TABLE public.badchannels OWNER TO apache;

--
-- Name: flags; Type: TABLE; Schema: public; Owner: apache; Tablespace: 
--

CREATE TABLE flags (
    ghc integer NOT NULL,
    dbid integer NOT NULL,
    flag character varying(20) NOT NULL
);


ALTER TABLE public.flags OWNER TO apache;

--
-- Name: runs; Type: TABLE; Schema: public; Owner: apache; Tablespace: 
--

CREATE TABLE runs (
    ghc integer NOT NULL,
    run integer NOT NULL,
    type character varying(50) NOT NULL,
    comment text
);


ALTER TABLE public.runs OWNER TO apache;

--
-- Name: valuekeys; Type: TABLE; Schema: public; Owner: apache; Tablespace: 
--

CREATE TABLE valuekeys (
    keyid integer NOT NULL,
    key character varying(25) NOT NULL
);


ALTER TABLE public.valuekeys OWNER TO apache;

--
-- Name: values; Type: TABLE; Schema: public; Owner: apache; Tablespace: 
--

CREATE TABLE "values" (
    ghc integer NOT NULL,
    dbid integer NOT NULL,
    keyid integer NOT NULL,
    value real NOT NULL
);


ALTER TABLE public."values" OWNER TO apache;

--
-- Name: badchannel_pkey; Type: CONSTRAINT; Schema: public; Owner: apache; Tablespace: 
--

ALTER TABLE ONLY badchannels
    ADD CONSTRAINT badchannel_pkey PRIMARY KEY (dbid);


--
-- Name: flags_pkey; Type: CONSTRAINT; Schema: public; Owner: apache; Tablespace: 
--

ALTER TABLE ONLY flags
    ADD CONSTRAINT flags_pkey PRIMARY KEY (ghc, dbid, flag);


--
-- Name: runs_pkey; Type: CONSTRAINT; Schema: public; Owner: apache; Tablespace: 
--

ALTER TABLE ONLY runs
    ADD CONSTRAINT runs_pkey PRIMARY KEY (ghc, run);


--
-- Name: valuekeys_pkey; Type: CONSTRAINT; Schema: public; Owner: apache; Tablespace: 
--

ALTER TABLE ONLY valuekeys
    ADD CONSTRAINT valuekeys_pkey PRIMARY KEY (keyid);


--
-- Name: values_pkey; Type: CONSTRAINT; Schema: public; Owner: apache; Tablespace: 
--

ALTER TABLE ONLY "values"
    ADD CONSTRAINT values_pkey PRIMARY KEY (ghc, dbid, keyid);


--
-- Name: values_keyid_fkey; Type: FK CONSTRAINT; Schema: public; Owner: apache
--

ALTER TABLE ONLY "values"
    ADD CONSTRAINT values_keyid_fkey FOREIGN KEY (keyid) REFERENCES valuekeys(keyid);


--
-- Name: public; Type: ACL; Schema: -; Owner: postgres
--

REVOKE ALL ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON SCHEMA public FROM postgres;
GRANT ALL ON SCHEMA public TO postgres;
GRANT ALL ON SCHEMA public TO PUBLIC;


--
-- Name: badchannels; Type: ACL; Schema: public; Owner: apache
--

REVOKE ALL ON TABLE badchannels FROM PUBLIC;
REVOKE ALL ON TABLE badchannels FROM apache;
GRANT ALL ON TABLE badchannels TO apache;
GRANT SELECT ON TABLE badchannels TO pfgreadonly;


--
-- Name: flags; Type: ACL; Schema: public; Owner: apache
--

REVOKE ALL ON TABLE flags FROM PUBLIC;
REVOKE ALL ON TABLE flags FROM apache;
GRANT ALL ON TABLE flags TO apache;
GRANT SELECT ON TABLE flags TO pfgreadonly;


--
-- Name: runs; Type: ACL; Schema: public; Owner: apache
--

REVOKE ALL ON TABLE runs FROM PUBLIC;
REVOKE ALL ON TABLE runs FROM apache;
GRANT ALL ON TABLE runs TO apache;
GRANT SELECT ON TABLE runs TO pfgreadonly;


--
-- Name: valuekeys; Type: ACL; Schema: public; Owner: apache
--

REVOKE ALL ON TABLE valuekeys FROM PUBLIC;
REVOKE ALL ON TABLE valuekeys FROM apache;
GRANT ALL ON TABLE valuekeys TO apache;
GRANT SELECT ON TABLE valuekeys TO pfgreadonly;


--
-- Name: values; Type: ACL; Schema: public; Owner: apache
--

REVOKE ALL ON TABLE "values" FROM PUBLIC;
REVOKE ALL ON TABLE "values" FROM apache;
GRANT ALL ON TABLE "values" TO apache;
GRANT SELECT ON TABLE "values" TO pfgreadonly;


--
-- PostgreSQL database dump complete
--

END;
