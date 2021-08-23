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
    join_status character varying(8) DEFAULT 'open'::character varying NOT NULL,
    base character varying(15),
    base_set boolean DEFAULT false,
    min_level smallint DEFAULT 0 NOT NULL
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
    prestige smallint DEFAULT 0 NOT NULL,
    gravitas integer DEFAULT 0 NOT NULL,
    CONSTRAINT check_positive CHECK ((gravitas >= 0))
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
-- Name: area_attacks; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.area_attacks (
    id bigint NOT NULL,
    area character varying(15) NOT NULL,
    attacker bigint,
    defender bigint,
    winner bigint,
    battle_date timestamp without time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.area_attacks OWNER TO postgres;

--
-- Name: area_attacks_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.area_attacks_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.area_attacks_id_seq OWNER TO postgres;

--
-- Name: area_attacks_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.area_attacks_id_seq OWNED BY public.area_attacks.id;


--
-- Name: area_control; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.area_control (
    id bigint NOT NULL,
    area character varying(15) NOT NULL,
    owner bigint,
    reign_begin timestamp without time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.area_control OWNER TO postgres;

--
-- Name: area_control_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.area_control_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.area_control_id_seq OWNER TO postgres;

--
-- Name: area_control_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.area_control_id_seq OWNED BY public.area_control.id;


--
-- Name: brotherhood_champions; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.brotherhood_champions (
    id bigint NOT NULL,
    guild_id bigint NOT NULL,
    champ1 bigint,
    champ2 bigint,
    champ3 bigint
);


ALTER TABLE public.brotherhood_champions OWNER TO postgres;

--
-- Name: brotherhood_champions_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.brotherhood_champions_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.brotherhood_champions_id_seq OWNER TO postgres;

--
-- Name: brotherhood_champions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.brotherhood_champions_id_seq OWNED BY public.brotherhood_champions.id;


--
-- Name: class_estate; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.class_estate (
    id bigint NOT NULL,
    user_id bigint NOT NULL,
    name character varying(32) DEFAULT 'My Practice'::character varying,
    type character varying(15),
    adventure bigint,
    image text
);


ALTER TABLE public.class_estate OWNER TO postgres;

--
-- Name: class_estate_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.class_estate_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.class_estate_id_seq OWNER TO postgres;

--
-- Name: class_estate_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.class_estate_id_seq OWNED BY public.class_estate.id;


--
-- Name: comptroller_bonuses; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.comptroller_bonuses (
    id bigint NOT NULL,
    comptroller_id bigint NOT NULL,
    bonus character varying(6),
    bonus_xp integer DEFAULT 0,
    is_set boolean DEFAULT false NOT NULL,
    guild_id bigint
);


ALTER TABLE public.comptroller_bonuses OWNER TO postgres;

--
-- Name: comptroller_bonuses_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.comptroller_bonuses_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.comptroller_bonuses_id_seq OWNER TO postgres;

--
-- Name: comptroller_bonuses_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.comptroller_bonuses_id_seq OWNED BY public.comptroller_bonuses.id;


--
-- Name: guild_bank_account; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.guild_bank_account (
    id bigint NOT NULL,
    user_id bigint NOT NULL,
    account_funds bigint DEFAULT 0 NOT NULL
);


ALTER TABLE public.guild_bank_account OWNER TO postgres;

--
-- Name: guild_bank_account_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.guild_bank_account_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.guild_bank_account_id_seq OWNER TO postgres;

--
-- Name: guild_bank_account_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.guild_bank_account_id_seq OWNED BY public.guild_bank_account.id;


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
-- Name: guild_joins; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.guild_joins (
    id bigint NOT NULL,
    user_id bigint NOT NULL,
    guild_id bigint NOT NULL,
    join_date timestamp without time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.guild_joins OWNER TO postgres;

--
-- Name: guild_joins_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.guild_joins_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.guild_joins_id_seq OWNER TO postgres;

--
-- Name: guild_joins_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.guild_joins_id_seq OWNED BY public.guild_joins.id;


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
-- Name: officeholders; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.officeholders (
    id bigint NOT NULL,
    officeholder bigint NOT NULL,
    office character varying(12) NOT NULL,
    setdate date DEFAULT CURRENT_DATE
);


ALTER TABLE public.officeholders OWNER TO postgres;

--
-- Name: officeholders_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.officeholders_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.officeholders_id_seq OWNER TO postgres;

--
-- Name: officeholders_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.officeholders_id_seq OWNED BY public.officeholders.id;


--
-- Name: prefixes; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.prefixes (
    server bigint,
    prefix character varying(10) DEFAULT '%'::character varying NOT NULL
);


ALTER TABLE public.prefixes OWNER TO postgres;

--
-- Name: raid_logs; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.raid_logs (
    id bigint NOT NULL,
    user_id bigint NOT NULL,
    attack_damage smallint NOT NULL
);


ALTER TABLE public.raid_logs OWNER TO postgres;

--
-- Name: raid_logs_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.raid_logs_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.raid_logs_id_seq OWNER TO postgres;

--
-- Name: raid_logs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.raid_logs_id_seq OWNED BY public.raid_logs.id;


--
-- Name: reminders; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.reminders (
    id bigint NOT NULL,
    starttime bigint NOT NULL,
    endtime bigint NOT NULL,
    user_id bigint NOT NULL,
    content character varying(255)
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
-- Name: tax_rates; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.tax_rates (
    id bigint NOT NULL,
    tax_rate numeric(3,2) DEFAULT 5 NOT NULL,
    setby bigint,
    setdate timestamp without time zone DEFAULT now()
);


ALTER TABLE public.tax_rates OWNER TO postgres;

--
-- Name: tax_rates_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.tax_rates_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.tax_rates_id_seq OWNER TO postgres;

--
-- Name: tax_rates_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.tax_rates_id_seq OWNED BY public.tax_rates.id;


--
-- Name: tax_transactions; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.tax_transactions (
    id bigint NOT NULL,
    "time" timestamp without time zone DEFAULT now(),
    user_id bigint NOT NULL,
    before_tax integer NOT NULL,
    tax_amount integer NOT NULL,
    tax_rate numeric(3,2)
);


ALTER TABLE public.tax_transactions OWNER TO postgres;

--
-- Name: tax_transactions_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.tax_transactions_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.tax_transactions_id_seq OWNER TO postgres;

--
-- Name: tax_transactions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.tax_transactions_id_seq OWNED BY public.tax_transactions.id;


--
-- Name: acolytes instance_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.acolytes ALTER COLUMN instance_id SET DEFAULT nextval('public."Acolytes_instance_id_seq"'::regclass);


--
-- Name: area_attacks id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.area_attacks ALTER COLUMN id SET DEFAULT nextval('public.area_attacks_id_seq'::regclass);


--
-- Name: area_control id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.area_control ALTER COLUMN id SET DEFAULT nextval('public.area_control_id_seq'::regclass);


--
-- Name: brotherhood_champions id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.brotherhood_champions ALTER COLUMN id SET DEFAULT nextval('public.brotherhood_champions_id_seq'::regclass);


--
-- Name: class_estate id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.class_estate ALTER COLUMN id SET DEFAULT nextval('public.class_estate_id_seq'::regclass);


--
-- Name: comptroller_bonuses id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.comptroller_bonuses ALTER COLUMN id SET DEFAULT nextval('public.comptroller_bonuses_id_seq'::regclass);


--
-- Name: guild_bank_account id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.guild_bank_account ALTER COLUMN id SET DEFAULT nextval('public.guild_bank_account_id_seq'::regclass);


--
-- Name: guild_joins id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.guild_joins ALTER COLUMN id SET DEFAULT nextval('public.guild_joins_id_seq'::regclass);


--
-- Name: guilds guild_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.guilds ALTER COLUMN guild_id SET DEFAULT nextval('public."Guilds_guild_id_seq"'::regclass);


--
-- Name: items item_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.items ALTER COLUMN item_id SET DEFAULT nextval('public."Items_item_id_seq"'::regclass);


--
-- Name: officeholders id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.officeholders ALTER COLUMN id SET DEFAULT nextval('public.officeholders_id_seq'::regclass);


--
-- Name: players num; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.players ALTER COLUMN num SET DEFAULT nextval('public."Players_num_seq"'::regclass);


--
-- Name: raid_logs id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.raid_logs ALTER COLUMN id SET DEFAULT nextval('public.raid_logs_id_seq'::regclass);


--
-- Name: reminders id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.reminders ALTER COLUMN id SET DEFAULT nextval('public.reminders_id_seq'::regclass);


--
-- Name: tax_rates id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tax_rates ALTER COLUMN id SET DEFAULT nextval('public.tax_rates_id_seq'::regclass);


--
-- Name: tax_transactions id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tax_transactions ALTER COLUMN id SET DEFAULT nextval('public.tax_transactions_id_seq'::regclass);


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
-- Name: area_attacks area_attacks_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.area_attacks
    ADD CONSTRAINT area_attacks_pkey PRIMARY KEY (id);


--
-- Name: area_control area_control_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.area_control
    ADD CONSTRAINT area_control_pkey PRIMARY KEY (id);


--
-- Name: brotherhood_champions brotherhood_champions_guild_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.brotherhood_champions
    ADD CONSTRAINT brotherhood_champions_guild_id_key UNIQUE (guild_id);


--
-- Name: brotherhood_champions brotherhood_champions_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.brotherhood_champions
    ADD CONSTRAINT brotherhood_champions_pkey PRIMARY KEY (id);


--
-- Name: class_estate class_estate_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.class_estate
    ADD CONSTRAINT class_estate_pkey PRIMARY KEY (id);


--
-- Name: class_estate class_estate_user_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.class_estate
    ADD CONSTRAINT class_estate_user_id_key UNIQUE (user_id);


--
-- Name: comptroller_bonuses comptroller_bonuses_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.comptroller_bonuses
    ADD CONSTRAINT comptroller_bonuses_pkey PRIMARY KEY (id);


--
-- Name: guild_bank_account guild_bank_account_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.guild_bank_account
    ADD CONSTRAINT guild_bank_account_pkey PRIMARY KEY (id);


--
-- Name: guild_bank_account guild_bank_account_user_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.guild_bank_account
    ADD CONSTRAINT guild_bank_account_user_id_key UNIQUE (user_id);


--
-- Name: guild_joins guild_joins_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.guild_joins
    ADD CONSTRAINT guild_joins_pkey PRIMARY KEY (id);


--
-- Name: officeholders officeholders_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.officeholders
    ADD CONSTRAINT officeholders_pkey PRIMARY KEY (id);


--
-- Name: raid_logs raid_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.raid_logs
    ADD CONSTRAINT raid_logs_pkey PRIMARY KEY (id);


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
-- Name: tax_rates tax_rates_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tax_rates
    ADD CONSTRAINT tax_rates_pkey PRIMARY KEY (id);


--
-- Name: tax_transactions tax_transactions_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tax_transactions
    ADD CONSTRAINT tax_transactions_pkey PRIMARY KEY (id);


--
-- Name: strategy strategy_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.strategy
    ADD CONSTRAINT strategy_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.players(user_id);


--
-- PostgreSQL database dump complete
--

