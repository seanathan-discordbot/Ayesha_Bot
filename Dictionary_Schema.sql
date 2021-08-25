--
-- PostgreSQL database dump
--

-- Dumped from database version 13.1
-- Dumped by pg_dump version 13.1

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: lightning_wins; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.lightning_wins (
    id bigint NOT NULL,
    player bigint NOT NULL,
    win_amount integer DEFAULT 1 NOT NULL
);


ALTER TABLE public.lightning_wins OWNER TO postgres;

--
-- Name: lightning_wins_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.lightning_wins_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.lightning_wins_id_seq OWNER TO postgres;

--
-- Name: lightning_wins_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.lightning_wins_id_seq OWNED BY public.lightning_wins.id;


--
-- Name: public_wins; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.public_wins (
    id bigint NOT NULL,
    player bigint NOT NULL,
    win_amount integer DEFAULT 1 NOT NULL
);


ALTER TABLE public.public_wins OWNER TO postgres;

--
-- Name: public_wins_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.public_wins_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.public_wins_id_seq OWNER TO postgres;

--
-- Name: public_wins_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.public_wins_id_seq OWNED BY public.public_wins.id;


--
-- Name: scrabble_wins; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.scrabble_wins (
    id bigint NOT NULL,
    player bigint NOT NULL,
    score integer DEFAULT 0 NOT NULL
);


ALTER TABLE public.scrabble_wins OWNER TO postgres;

--
-- Name: scrabble_wins_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.scrabble_wins_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.scrabble_wins_id_seq OWNER TO postgres;

--
-- Name: scrabble_wins_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.scrabble_wins_id_seq OWNED BY public.scrabble_wins.id;


--
-- Name: solo_wins; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.solo_wins (
    id bigint NOT NULL,
    player bigint NOT NULL,
    score integer DEFAULT 0 NOT NULL
);


ALTER TABLE public.solo_wins OWNER TO postgres;

--
-- Name: solo_wins_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.solo_wins_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.solo_wins_id_seq OWNER TO postgres;

--
-- Name: solo_wins_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.solo_wins_id_seq OWNED BY public.solo_wins.id;


--
-- Name: word_list; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.word_list (
    id bigint NOT NULL,
    word character varying(32)
);


ALTER TABLE public.word_list OWNER TO postgres;

--
-- Name: word_list_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.word_list_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.word_list_id_seq OWNER TO postgres;

--
-- Name: word_list_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.word_list_id_seq OWNED BY public.word_list.id;


--
-- Name: lightning_wins id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.lightning_wins ALTER COLUMN id SET DEFAULT nextval('public.lightning_wins_id_seq'::regclass);


--
-- Name: public_wins id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.public_wins ALTER COLUMN id SET DEFAULT nextval('public.public_wins_id_seq'::regclass);


--
-- Name: scrabble_wins id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.scrabble_wins ALTER COLUMN id SET DEFAULT nextval('public.scrabble_wins_id_seq'::regclass);


--
-- Name: solo_wins id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.solo_wins ALTER COLUMN id SET DEFAULT nextval('public.solo_wins_id_seq'::regclass);


--
-- Name: word_list id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.word_list ALTER COLUMN id SET DEFAULT nextval('public.word_list_id_seq'::regclass);


--
-- Name: lightning_wins lightning_wins_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.lightning_wins
    ADD CONSTRAINT lightning_wins_pkey PRIMARY KEY (id);


--
-- Name: lightning_wins lightning_wins_player_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.lightning_wins
    ADD CONSTRAINT lightning_wins_player_key UNIQUE (player);


--
-- Name: public_wins public_wins_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.public_wins
    ADD CONSTRAINT public_wins_pkey PRIMARY KEY (id);


--
-- Name: public_wins public_wins_player_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.public_wins
    ADD CONSTRAINT public_wins_player_key UNIQUE (player);


--
-- Name: scrabble_wins scrabble_wins_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.scrabble_wins
    ADD CONSTRAINT scrabble_wins_pkey PRIMARY KEY (id);


--
-- Name: solo_wins solo_wins_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.solo_wins
    ADD CONSTRAINT solo_wins_pkey PRIMARY KEY (id);


--
-- Name: word_list word_list_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.word_list
    ADD CONSTRAINT word_list_pkey PRIMARY KEY (id);


--
-- PostgreSQL database dump complete
--

