CREATE DATABASE IF NOT EXISTS deezerparsing CHARACTER SET utf8 COLLATE utf8_general_ci;
USE deezerparsing;
CREATE TABLE Artists(Id INT PRIMARY KEY, Title VARCHAR(255), ImageMed VARCHAR(255), FULLTEXT (Title));
CREATE TABLE Albums(Id INT PRIMARY KEY, ArtistId INT, Title VARCHAR(255), ImageMed VARCHAR(255), Genre VARCHAR(255), Fans INT, ReleaseDate DATE, FULLTEXT (Title));
DELIMITER $$
CREATE PROCEDURE `insert_artist` (IN artid INT, IN arttitle VARCHAR(255), IN artimage VARCHAR(255))
BEGIN
   INSERT IGNORE INTO Artists(Id, Title, ImageMed)
   VALUES
      (
         artid, arttitle, artimage
      );
END;
$$
DELIMITER $$
CREATE PROCEDURE `insert_album` (IN albid INT, IN artid INT, IN albtitle VARCHAR(255), IN albimage VARCHAR(255), IN albgenre VARCHAR(255), IN albfans INT, IN albrelease DATE)
BEGIN
   INSERT IGNORE INTO Albums(Id, ArtistId, Title, ImageMed, Genre, Fans, ReleaseDate)
   VALUES
      (
         albid, artid, albtitle, albimage, albgenre, albfans, albrelease
      );
END;
$$
DELIMITER $$
CREATE PROCEDURE `get_artist_by_name` (IN arttitle VARCHAR(255))
BEGIN
   SELECT
      *
   FROM
      Artists
   WHERE Title LIKE CONCAT('%', arttitle , '%');
END;
$$
DELIMITER $$
CREATE PROCEDURE `get_artist_by_id` (IN artid VARCHAR(255))
BEGIN
   SELECT
      *
   FROM
      Artists
   WHERE Id = artid;
END;
$$
DELIMITER $$
CREATE PROCEDURE `get_album_by_id` (IN albid INT)
BEGIN
   SELECT
      Albums.Id,Albums.Title,Albums.ImageMed,Albums.Genre,Albums.Fans,Albums.ReleaseDate,Artists.Title
   FROM
      Albums,Artists
   WHERE Albums.Id = albid;
END;
$$
DELIMITER $$
CREATE PROCEDURE `get_artists` (IN delim VARCHAR(255), IN start INT, IN lim INT)
BEGIN
   SELECT
      Artists.Id,Artists.Title,Artists.ImageMed,GROUP_CONCAT(Albums.Title, delim)
   FROM
      Artists,Albums
   WHERE Artists.Id=Albums.ArtistId GROUP BY Artists.Id
   LIMIT start, lim;
END;
$$
DELIMITER $$
CREATE PROCEDURE `get_albums` (IN start INT, IN lim INT)
BEGIN
   SELECT
      Albums.Id,Albums.Title,Albums.ImageMed,Albums.Genre,Albums.Fans,Albums.ReleaseDate,Artists.Title
   FROM
      Artists,Albums
   WHERE Albums.ArtistId = Artists.Id
   LIMIT start, lim;
END;
$$
