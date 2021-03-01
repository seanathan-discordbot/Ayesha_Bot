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
-- Name: acolytes; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.acolytes (
    instance_id bigint NOT NULL,
    owner_id bigint NOT NULL,
    acolyte_name character varying(20) NOT NULL,
    lvl integer DEFAULT 0 NOT NULL,
    xp integer DEFAULT 0 NOT NULL,
    duplicate smallint DEFAULT 0 NOT NULL,
    is_equipped smallint DEFAULT 0 NOT NULL
);


ALTER TABLE public.acolytes OWNER TO postgres;

--
-- Name: Acolytes_instance_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public."Acolytes_instance_id_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public."Acolytes_instance_id_seq" OWNER TO postgres;

--
-- Name: Acolytes_instance_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public."Acolytes_instance_id_seq" OWNED BY public.acolytes.instance_id;


--
-- Name: guilds; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.guilds (
    guild_id bigint NOT NULL,
    guild_name character varying(32) NOT NULL,
    guild_type character varying(15) NOT NULL,
    guild_xp integer DEFAULT 0 NOT NULL,
    leader_id bigint NOT NULL,
    guild_desc character varying(256),
    guild_icon text NOT NULL,
    join_status character varying(8) DEFAULT 'open'::character varying NOT NULL
);


ALTER TABLE public.guilds OWNER TO postgres;

--
-- Name: Guilds_guild_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public."Guilds_guild_id_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public."Guilds_guild_id_seq" OWNER TO postgres;

--
-- Name: Guilds_guild_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public."Guilds_guild_id_seq" OWNED BY public.guilds.guild_id;


--
-- Name: items; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.items (
    item_id bigint NOT NULL,
    weapontype character varying(15) NOT NULL,
    owner_id bigint NOT NULL,
    attack smallint NOT NULL,
    crit smallint NOT NULL,
    weapon_name character varying(20) NOT NULL,
    rarity character varying(10) NOT NULL,
    is_equipped boolean DEFAULT false NOT NULL
);


ALTER TABLE public.items OWNER TO postgres;

--
-- Name: Items_item_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public."Items_item_id_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public."Items_item_id_seq" OWNER TO postgres;

--
-- Name: Items_item_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public."Items_item_id_seq" OWNED BY public.items.item_id;


--
-- Name: players; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.players (
    num bigint NOT NULL,
    user_id bigint NOT NULL,
    user_name character varying(32) NOT NULL,
    xp integer DEFAULT 0 NOT NULL,
    lvl integer DEFAULT 0 NOT NULL,
    equipped_item integer,
    acolyte1 integer,
    acolyte2 integer,
    guild integer,
    guild_rank character varying(8),
    gold integer DEFAULT 500 NOT NULL,
    occupation character varying(15),
    origin character varying(15),
    loc character varying(15) DEFAULT 'Aramithea'::character varying NOT NULL,
    pvpwins integer DEFAULT 0 NOT NULL,
    pvpfights integer DEFAULT 0 NOT NULL,
    bosswins integer DEFAULT 0 NOT NULL,
    bossfights integer DEFAULT 0 NOT NULL,
    rubidic integer DEFAULT 10 NOT NULL,
    pitycounter smallint DEFAULT 0 NOT NULL,
    adventure bigint,
    destination character varying(15),
    prestige smallint DEFAULT 0 NOT NULL
);


ALTER TABLE public.players OWNER TO postgres;

--
-- Name: Players_num_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public."Players_num_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public."Players_num_seq" OWNER TO postgres;

--
-- Name: Players_num_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public."Players_num_seq" OWNED BY public.players.num;


--
-- Name: guild_levels; Type: VIEW; Schema: public; Owner: postgres
--

CREATE VIEW public.guild_levels AS
 SELECT guilds.guild_id,
    (guilds.guild_xp / 1000000) AS guild_level
   FROM public.guilds;


ALTER TABLE public.guild_levels OWNER TO postgres;

--
-- Name: guild_capacities; Type: VIEW; Schema: public; Owner: postgres
--

CREATE VIEW public.guild_capacities AS
 SELECT guild_levels.guild_id,
    ((guild_levels.guild_level * 2) + 30) AS capacity
   FROM public.guild_levels;


ALTER TABLE public.guild_capacities OWNER TO postgres;

--
-- Name: guild_membercount; Type: VIEW; Schema: public; Owner: postgres
--

CREATE VIEW public.guild_membercount AS
 SELECT players.guild AS guild_id,
    count(*) AS member_count
   FROM public.players
  GROUP BY players.guild;


ALTER TABLE public.guild_membercount OWNER TO postgres;

--
-- Name: prefixes; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.prefixes (
    server bigint,
    prefix character varying(10) DEFAULT '%'::character varying NOT NULL
);


ALTER TABLE public.prefixes OWNER TO postgres;

--
-- Name: reminders; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.reminders (
    id bigint NOT NULL,
    starttime bigint NOT NULL,
    endtime bigint NOT NULL,
    user_id bigint NOT NULL,
    content character varying(100)
);


ALTER TABLE public.reminders OWNER TO postgres;

--
-- Name: reminders_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.reminders_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.reminders_id_seq OWNER TO postgres;

--
-- Name: reminders_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.reminders_id_seq OWNED BY public.reminders.id;


--
-- Name: resources; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.resources (
    user_id bigint NOT NULL,
    fur integer DEFAULT 0 NOT NULL,
    bone integer DEFAULT 0 NOT NULL,
    iron integer DEFAULT 0 NOT NULL,
    silver integer DEFAULT 0 NOT NULL,
    wood integer DEFAULT 0 NOT NULL,
    wheat integer DEFAULT 0 NOT NULL,
    oat integer DEFAULT 0 NOT NULL,
    reeds integer DEFAULT 0 NOT NULL,
    pine integer DEFAULT 0 NOT NULL,
    moss integer DEFAULT 0 NOT NULL,
    cacao integer DEFAULT 0 NOT NULL
);


ALTER TABLE public.resources OWNER TO postgres;

--
-- Name: strategy; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.strategy (
    user_id bigint NOT NULL,
    attack smallint DEFAULT 60 NOT NULL,
    block smallint DEFAULT 15 NOT NULL,
    parry smallint DEFAULT 15 NOT NULL,
    heal smallint DEFAULT 5 NOT NULL,
    bide smallint DEFAULT 5 NOT NULL
);


ALTER TABLE public.strategy OWNER TO postgres;

--
-- Name: acolytes instance_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.acolytes ALTER COLUMN instance_id SET DEFAULT nextval('public."Acolytes_instance_id_seq"'::regclass);


--
-- Name: guilds guild_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.guilds ALTER COLUMN guild_id SET DEFAULT nextval('public."Guilds_guild_id_seq"'::regclass);


--
-- Name: items item_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.items ALTER COLUMN item_id SET DEFAULT nextval('public."Items_item_id_seq"'::regclass);


--
-- Name: players num; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.players ALTER COLUMN num SET DEFAULT nextval('public."Players_num_seq"'::regclass);


--
-- Name: reminders id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.reminders ALTER COLUMN id SET DEFAULT nextval('public.reminders_id_seq'::regclass);


--
-- Name: acolytes Acolytes_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.acolytes
    ADD CONSTRAINT "Acolytes_pkey" PRIMARY KEY (instance_id);


--
-- Name: guilds Guilds_guild_name_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.guilds
    ADD CONSTRAINT "Guilds_guild_name_key" UNIQUE (guild_name);


--
-- Name: guilds Guilds_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.guilds
    ADD CONSTRAINT "Guilds_pkey" PRIMARY KEY (guild_id);


--
-- Name: items Items_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.items
    ADD CONSTRAINT "Items_pkey" PRIMARY KEY (item_id);


--
-- Name: players Players_acolyte1_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.players
    ADD CONSTRAINT "Players_acolyte1_key" UNIQUE (acolyte1);


--
-- Name: players Players_acolyte2_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.players
    ADD CONSTRAINT "Players_acolyte2_key" UNIQUE (acolyte2);


--
-- Name: players Players_equipped_item_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.players
    ADD CONSTRAINT "Players_equipped_item_key" UNIQUE (equipped_item);


--
-- Name: players Players_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.players
    ADD CONSTRAINT "Players_pkey" PRIMARY KEY (num);


--
-- Name: players Players_user_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.players
    ADD CONSTRAINT "Players_user_id_key" UNIQUE (user_id);


--
-- Name: resources Resources_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.resources
    ADD CONSTRAINT "Resources_pkey" PRIMARY KEY (user_id);


--
-- Name: reminders reminders_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.reminders
    ADD CONSTRAINT reminders_pkey PRIMARY KEY (id);


--
-- Name: strategy strategy_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.strategy
    ADD CONSTRAINT strategy_pkey PRIMARY KEY (user_id);


--
-- Name: strategy strategy_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.strategy
    ADD CONSTRAINT strategy_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.players(user_id);


--
-- PostgreSQL database dump complete
--

