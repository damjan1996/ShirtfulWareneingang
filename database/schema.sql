-- RdScanner Datenbank Schema
-- Minimale Version für RFID & QR Scanner

-- Datenbank erstellen
IF NOT EXISTS (SELECT * FROM sys.databases WHERE name = 'RdScanner')
CREATE DATABASE [RdScanner];
GO

USE [RdScanner];
GO

-- ScannBenutzer Tabelle
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'ScannBenutzer')
CREATE TABLE dbo.ScannBenutzer (
    ID decimal(18,0) IDENTITY(1,1) NOT NULL PRIMARY KEY,
    Vorname varchar(255) NULL,
    Nachname varchar(255) NULL,
    Benutzer varchar(255) NULL,
    BenutzerName varchar(255) NULL,
    BenutzerPasswort varchar(255) NULL,
    Email varchar(255) NULL,
    EPC decimal(38,0) NULL,
    xStatus int NULL DEFAULT 0,
    xDatum datetime NULL DEFAULT GETDATE(),
    xDatumINT decimal(18,0) NULL,
    xBenutzer varchar(255) NULL,
    xVersion timestamp NOT NULL
);
GO

-- Sessions Tabelle
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Sessions')
CREATE TABLE dbo.Sessions (
    ID bigint IDENTITY(1,1) NOT NULL PRIMARY KEY,
    UserID decimal(18,0) NOT NULL,
    StartTS datetime2 NOT NULL DEFAULT SYSDATETIME(),
    EndTS datetime2 NULL,
    DurationSec AS DATEDIFF(SECOND, StartTS, ISNULL(EndTS, SYSDATETIME())),
    Active bit NOT NULL DEFAULT 1
);
GO

-- QrScans Tabelle
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'QrScans')
CREATE TABLE dbo.QrScans (
    ID bigint IDENTITY(1,1) NOT NULL PRIMARY KEY,
    SessionID bigint NOT NULL,
    RawPayload nvarchar(MAX) NOT NULL,
    PayloadJson AS (
        CASE
            WHEN ISJSON(RawPayload) = 1 THEN RawPayload
            ELSE NULL
        END
    ),
    CapturedTS datetime2 NOT NULL DEFAULT SYSDATETIME(),
    Valid bit NOT NULL DEFAULT 1
);
GO

-- Optionale Tabellen für erweiterte Funktionen
-- ScannTyp
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'ScannTyp')
CREATE TABLE dbo.ScannTyp (
    ID decimal(18,0) IDENTITY(1,1) NOT NULL PRIMARY KEY,
    Bezeichnung varchar(255) NULL,
    xStatus int NULL DEFAULT 0,
    xDatum datetime NULL DEFAULT GETDATE(),
    xDatumINT decimal(18,0) NULL,
    xBenutzer varchar(255) NULL,
    xVersion timestamp NOT NULL
);
GO

-- ScannKopf
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'ScannKopf')
CREATE TABLE dbo.ScannKopf (
    ID decimal(18,0) IDENTITY(1,1) NOT NULL PRIMARY KEY,
    TagesDatum date NULL DEFAULT CAST(GETDATE() AS DATE),
    TagesDatumINT int NULL,
    Datum datetime NULL DEFAULT GETDATE(),
    DatumINT decimal(18,0) NULL,
    EPC decimal(38,0) NULL,
    Arbeitsplatz varchar(255) NULL,
    ScannTyp_ID decimal(18,0) NULL,
    xStatus int NULL DEFAULT 0,
    xDatum datetime NULL DEFAULT GETDATE(),
    xDatumINT decimal(18,0) NULL,
    xBenutzer varchar(255) NULL,
    xVersion timestamp NOT NULL
);
GO

-- ScannPosition
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'ScannPosition')
CREATE TABLE dbo.ScannPosition (
    ID decimal(18,0) IDENTITY(1,1) NOT NULL PRIMARY KEY,
    ScannKopf_ID decimal(18,0) NOT NULL,
    TagesDatum date NULL DEFAULT CAST(GETDATE() AS DATE),
    TagesDatumINT int NULL,
    Datum datetime NULL DEFAULT GETDATE(),
    DatumINT decimal(18,0) NULL,
    Kunde varchar(255) NULL,
    Auftragsnummer varchar(255) NULL,
    Paketnummer varchar(255) NULL,
    Zusatzinformtion varchar(255) NULL,
    xStatus int NULL DEFAULT 0,
    xDatum datetime NULL DEFAULT GETDATE(),
    xDatumINT decimal(18,0) NULL,
    xBenutzer varchar(255) NULL,
    xVersion timestamp NOT NULL
);
GO

-- Indizes
CREATE UNIQUE INDEX UQ_Sessions_ActiveUser ON dbo.Sessions(UserID) WHERE Active = 1;
CREATE INDEX IX_ScannBenutzer_EPC ON dbo.ScannBenutzer(EPC);
CREATE INDEX IX_QrScans_SessionID ON dbo.QrScans(SessionID);
CREATE INDEX IX_QrScans_CapturedTS ON dbo.QrScans(CapturedTS);
GO

-- Foreign Keys
ALTER TABLE dbo.Sessions
ADD CONSTRAINT FK_Sessions_Users FOREIGN KEY (UserID) REFERENCES dbo.ScannBenutzer(ID);

ALTER TABLE dbo.QrScans
ADD CONSTRAINT FK_QrScans_Sessions FOREIGN KEY (SessionID) REFERENCES dbo.Sessions(ID);

ALTER TABLE dbo.ScannKopf
ADD CONSTRAINT FK_ScannKopf_ScannTyp FOREIGN KEY (ScannTyp_ID) REFERENCES dbo.ScannTyp(ID);

ALTER TABLE dbo.ScannPosition
ADD CONSTRAINT FK_ScannPosition_ScannKopf FOREIGN KEY (ScannKopf_ID) REFERENCES dbo.ScannKopf(ID);
GO

-- Beispiel-Daten für ScannTyp
INSERT INTO dbo.ScannTyp (Bezeichnung, xBenutzer) VALUES
('Wareneingang', 'System'),
('Qualitätskontrolle', 'System'),
('Versand', 'System');
GO