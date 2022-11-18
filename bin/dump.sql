-- MySQL dump 10.13  Distrib 8.0.31, for Linux (x86_64)
--
-- Host: erpsystem.cc9d4uudotkz.ap-northeast-2.rds.amazonaws.com    Database: erpsystem
-- ------------------------------------------------------
-- Server version	8.0.28

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;
SET @MYSQLDUMP_TEMP_LOG_BIN = @@SESSION.SQL_LOG_BIN;
SET @@SESSION.SQL_LOG_BIN= 0;

--
-- GTID state at the beginning of the backup 
--

SET @@GLOBAL.GTID_PURGED=/*!80000 '+'*/ '';

--
-- Table structure for table `brand`
--

DROP TABLE IF EXISTS `brand`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `brand` (
  `brand_tag` varchar(4) NOT NULL,
  `brand_name` varchar(16) DEFAULT NULL,
  `use_flag` tinyint unsigned DEFAULT NULL,
  `description` varchar(128) DEFAULT NULL,
  `user_id` varchar(16) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,
  `register_date` varchar(32) DEFAULT NULL,
  PRIMARY KEY (`brand_tag`),
  KEY `brand_FK` (`user_id`),
  CONSTRAINT `brand_FK` FOREIGN KEY (`user_id`) REFERENCES `user` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `brand`
--

LOCK TABLES `brand` WRITE;
/*!40000 ALTER TABLE `brand` DISABLE KEYS */;
/*!40000 ALTER TABLE `brand` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `category`
--

DROP TABLE IF EXISTS `category`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `category` (
  `category_tag` varchar(4) NOT NULL,
  `category_name` varchar(16) DEFAULT NULL,
  `use_flag` tinyint unsigned DEFAULT NULL,
  `description` varchar(128) DEFAULT NULL,
  `user_id` varchar(16) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,
  `register_date` varchar(32) DEFAULT NULL,
  PRIMARY KEY (`category_tag`),
  KEY `category_FK` (`user_id`),
  CONSTRAINT `category_FK` FOREIGN KEY (`user_id`) REFERENCES `user` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `category`
--

LOCK TABLES `category` WRITE;
/*!40000 ALTER TABLE `category` DISABLE KEYS */;
/*!40000 ALTER TABLE `category` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `community_board`
--

DROP TABLE IF EXISTS `community_board`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `community_board` (
  `index` int unsigned NOT NULL AUTO_INCREMENT,
  `type` tinyint unsigned DEFAULT NULL COMMENT '1: 공지사항, 2: 상품등록, 3: 교환요청, 4: 문의사항, 5: 배송요청, 6: 회수요청, 7: 홀딩요청, 8: ERP 수정, 9: 기타, 10: 구매팀요청',
  `title` varchar(64) DEFAULT NULL,
  `content` varchar(1024) DEFAULT NULL,
  `user_id` varchar(16) DEFAULT NULL,
  `register_date` varchar(32) DEFAULT NULL,
  `view_count` int unsigned NOT NULL DEFAULT '0',
  PRIMARY KEY (`index`),
  KEY `community_board_FK` (`user_id`),
  CONSTRAINT `community_board_FK` FOREIGN KEY (`user_id`) REFERENCES `user` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `community_board`
--

LOCK TABLES `community_board` WRITE;
/*!40000 ALTER TABLE `community_board` DISABLE KEYS */;
/*!40000 ALTER TABLE `community_board` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `community_board_comment`
--

DROP TABLE IF EXISTS `community_board_comment`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `community_board_comment` (
  `comment_index` int unsigned NOT NULL AUTO_INCREMENT,
  `index` int unsigned DEFAULT NULL,
  `content` varchar(1024) DEFAULT NULL,
  `user_id` varchar(16) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `register_date` varchar(32) DEFAULT NULL,
  PRIMARY KEY (`comment_index`),
  KEY `community_board_comment_FK_1` (`index`),
  KEY `community_board_comment_FK` (`user_id`),
  CONSTRAINT `community_board_comment_FK` FOREIGN KEY (`user_id`) REFERENCES `user` (`user_id`) ON DELETE CASCADE ON UPDATE RESTRICT,
  CONSTRAINT `community_board_comment_FK_1` FOREIGN KEY (`index`) REFERENCES `community_board` (`index`) ON DELETE CASCADE ON UPDATE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `community_board_comment`
--

LOCK TABLES `community_board_comment` WRITE;
/*!40000 ALTER TABLE `community_board_comment` DISABLE KEYS */;
/*!40000 ALTER TABLE `community_board_comment` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `community_board_target`
--

DROP TABLE IF EXISTS `community_board_target`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `community_board_target` (
  `index` int unsigned NOT NULL,
  `office_tag` int unsigned NOT NULL,
  PRIMARY KEY (`index`,`office_tag`),
  KEY `community_board_target_FK_1` (`office_tag`),
  CONSTRAINT `community_board_target_FK` FOREIGN KEY (`index`) REFERENCES `community_board` (`index`),
  CONSTRAINT `community_board_target_FK_1` FOREIGN KEY (`office_tag`) REFERENCES `office` (`office_tag`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `community_board_target`
--

LOCK TABLES `community_board_target` WRITE;
/*!40000 ALTER TABLE `community_board_target` DISABLE KEYS */;
/*!40000 ALTER TABLE `community_board_target` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `cost_type`
--

DROP TABLE IF EXISTS `cost_type`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `cost_type` (
  `type` tinyint unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(8) DEFAULT NULL,
  PRIMARY KEY (`type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `cost_type`
--

LOCK TABLES `cost_type` WRITE;
/*!40000 ALTER TABLE `cost_type` DISABLE KEYS */;
/*!40000 ALTER TABLE `cost_type` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `goods`
--

DROP TABLE IF EXISTS `goods`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `goods` (
  `goods_tag` varchar(32) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `consignment_flag` tinyint unsigned DEFAULT NULL COMMENT '0: 위탁 아님, 1: 위탁',
  `part_number` varchar(32) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,
  `bl_number` varchar(100) DEFAULT NULL,
  `origin_name` varchar(16) DEFAULT NULL,
  `brand_tag` varchar(4) DEFAULT NULL,
  `category_tag` varchar(4) DEFAULT NULL,
  `office_tag` int unsigned DEFAULT NULL,
  `supplier_tag` int unsigned DEFAULT NULL,
  `color` varchar(16) DEFAULT NULL,
  `season` varchar(16) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,
  `sex` tinyint unsigned DEFAULT NULL,
  `size` varchar(8) DEFAULT NULL,
  `material` varchar(64) DEFAULT NULL,
  `status` tinyint unsigned DEFAULT NULL COMMENT '1: 스크래치, 2: 판매불가, 3: 폐기, 4: 정상재고, 5: 분실, 6: 정산대기, 7: 분배대기, 8: 회수완료, 9: 수선중, 10: 반품정산대기, 11: 판매완료, 12: 출고승인대기, 13: 고객반송대기',
  `stock_count` int unsigned DEFAULT NULL,
  `stocking_date` varchar(32) DEFAULT NULL,
  `import_date` varchar(32) DEFAULT NULL,
  `sale_date` varchar(32) DEFAULT NULL,
  `first_cost` bigint unsigned DEFAULT NULL,
  `cost` bigint unsigned DEFAULT NULL,
  `regular_cost` bigint unsigned DEFAULT NULL,
  `laprima_cost` bigint unsigned DEFAULT NULL,
  `event_cost` bigint unsigned DEFAULT NULL,
  `discount_cost` bigint unsigned DEFAULT NULL,
  `management_cost` bigint unsigned DEFAULT NULL,
  `management_cost_rate` float DEFAULT NULL,
  `department_store_cost` bigint unsigned DEFAULT NULL,
  `outlet_cost` bigint unsigned DEFAULT NULL,
  `user_id` varchar(16) DEFAULT NULL,
  `register_date` varchar(32) DEFAULT NULL,
  PRIMARY KEY (`goods_tag`),
  KEY `goods_FK` (`office_tag`),
  KEY `goods_FK_1` (`brand_tag`),
  KEY `goods_FK_2` (`category_tag`),
  KEY `goods_FK_3` (`supplier_tag`),
  KEY `goods_FK_4` (`origin_name`),
  CONSTRAINT `goods_FK` FOREIGN KEY (`office_tag`) REFERENCES `office` (`office_tag`),
  CONSTRAINT `goods_FK_1` FOREIGN KEY (`brand_tag`) REFERENCES `brand` (`brand_tag`),
  CONSTRAINT `goods_FK_2` FOREIGN KEY (`category_tag`) REFERENCES `category` (`category_tag`),
  CONSTRAINT `goods_FK_3` FOREIGN KEY (`supplier_tag`) REFERENCES `supplier` (`supplier_tag`),
  CONSTRAINT `goods_FK_4` FOREIGN KEY (`origin_name`) REFERENCES `origin` (`origin_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `goods`
--

LOCK TABLES `goods` WRITE;
/*!40000 ALTER TABLE `goods` DISABLE KEYS */;
/*!40000 ALTER TABLE `goods` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `goods_history`
--

DROP TABLE IF EXISTS `goods_history`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `goods_history` (
  `goods_tag` varchar(32) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `goods_history_index` int unsigned NOT NULL,
  `name` varchar(16) DEFAULT NULL,
  `description` varchar(256) DEFAULT NULL,
  `update_value` varchar(64) DEFAULT NULL,
  `update_method` tinyint unsigned DEFAULT NULL COMMENT '0: 일괄입력, 1: 직접입력',
  `status` tinyint unsigned DEFAULT NULL COMMENT '1: 스크래치, 2: 판매불가, 3: 폐기, 4: 정상재고, 5: 분실, 6: 정산대기, 7: 분배대기, 8: 회수완료, 9: 수선중, 10: 반품정산대기, 11: 판매완료, 12: 출고승인대기, 13: 고객반송대기',
  `user_id` varchar(16) DEFAULT NULL,
  `update_date` varchar(32) DEFAULT NULL,
  PRIMARY KEY (`goods_tag`,`goods_history_index`),
  KEY `goods_history_FK_1` (`user_id`),
  CONSTRAINT `goods_history_FK` FOREIGN KEY (`goods_tag`) REFERENCES `goods` (`goods_tag`),
  CONSTRAINT `goods_history_FK_1` FOREIGN KEY (`user_id`) REFERENCES `user` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `goods_history`
--

LOCK TABLES `goods_history` WRITE;
/*!40000 ALTER TABLE `goods_history` DISABLE KEYS */;
/*!40000 ALTER TABLE `goods_history` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `goods_image`
--

DROP TABLE IF EXISTS `goods_image`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `goods_image` (
  `goods_tag` varchar(32) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `goods_image_index` int unsigned NOT NULL,
  `image_path` varchar(256) DEFAULT NULL,
  `user_id` varchar(16) DEFAULT NULL,
  `register_date` varchar(32) DEFAULT NULL,
  PRIMARY KEY (`goods_tag`,`goods_image_index`),
  KEY `goods_image_FK_1` (`user_id`),
  CONSTRAINT `goods_image_FK` FOREIGN KEY (`goods_tag`) REFERENCES `goods` (`goods_tag`),
  CONSTRAINT `goods_image_FK_1` FOREIGN KEY (`user_id`) REFERENCES `user` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `goods_image`
--

LOCK TABLES `goods_image` WRITE;
/*!40000 ALTER TABLE `goods_image` DISABLE KEYS */;
/*!40000 ALTER TABLE `goods_image` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `office`
--

DROP TABLE IF EXISTS `office`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `office` (
  `office_tag` int unsigned NOT NULL AUTO_INCREMENT,
  `registration_number` varchar(16) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,
  `registration_name` varchar(32) DEFAULT NULL,
  `office_name` varchar(32) DEFAULT NULL,
  `representative` varchar(32) DEFAULT NULL,
  `description` varchar(128) DEFAULT NULL,
  `phone_number` varchar(16) DEFAULT NULL,
  `fax_number` varchar(16) DEFAULT NULL,
  `address` varchar(128) DEFAULT NULL,
  `business_status` varchar(32) DEFAULT NULL,
  `business_item` varchar(32) DEFAULT NULL,
  `use_flag` tinyint unsigned DEFAULT NULL,
  `user_id` varchar(16) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,
  `register_date` varchar(32) DEFAULT NULL,
  PRIMARY KEY (`office_tag`),
  KEY `office_FK` (`user_id`),
  CONSTRAINT `office_FK` FOREIGN KEY (`user_id`) REFERENCES `user` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `office`
--

LOCK TABLES `office` WRITE;
/*!40000 ALTER TABLE `office` DISABLE KEYS */;
/*!40000 ALTER TABLE `office` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `office_cost_type`
--

DROP TABLE IF EXISTS `office_cost_type`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `office_cost_type` (
  `office_tag` int unsigned NOT NULL,
  `type` tinyint unsigned NOT NULL,
  `user_id` varchar(16) DEFAULT NULL,
  `register_date` varchar(32) DEFAULT NULL,
  PRIMARY KEY (`office_tag`,`type`),
  KEY `office_cost_type_FK_1` (`type`),
  KEY `office_cost_type_FK_2` (`user_id`),
  CONSTRAINT `office_cost_type_FK` FOREIGN KEY (`office_tag`) REFERENCES `office` (`office_tag`),
  CONSTRAINT `office_cost_type_FK_1` FOREIGN KEY (`type`) REFERENCES `cost_type` (`type`),
  CONSTRAINT `office_cost_type_FK_2` FOREIGN KEY (`user_id`) REFERENCES `user` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `office_cost_type`
--

LOCK TABLES `office_cost_type` WRITE;
/*!40000 ALTER TABLE `office_cost_type` DISABLE KEYS */;
/*!40000 ALTER TABLE `office_cost_type` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `office_selling_type`
--

DROP TABLE IF EXISTS `office_selling_type`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `office_selling_type` (
  `office_tag` int unsigned NOT NULL,
  `type` tinyint unsigned NOT NULL,
  `user_id` varchar(16) DEFAULT NULL,
  `register_date` varchar(32) DEFAULT NULL,
  PRIMARY KEY (`office_tag`,`type`),
  KEY `office_selling_type_FK_1` (`type`),
  KEY `office_selling_type_FK_2` (`user_id`),
  CONSTRAINT `office_selling_type_FK` FOREIGN KEY (`office_tag`) REFERENCES `office` (`office_tag`),
  CONSTRAINT `office_selling_type_FK_1` FOREIGN KEY (`type`) REFERENCES `selling_type` (`type`),
  CONSTRAINT `office_selling_type_FK_2` FOREIGN KEY (`user_id`) REFERENCES `user` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `office_selling_type`
--

LOCK TABLES `office_selling_type` WRITE;
/*!40000 ALTER TABLE `office_selling_type` DISABLE KEYS */;
/*!40000 ALTER TABLE `office_selling_type` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `origin`
--

DROP TABLE IF EXISTS `origin`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `origin` (
  `origin_name` varchar(16) NOT NULL,
  `use_flag` tinyint unsigned DEFAULT NULL,
  `description` varchar(128) DEFAULT NULL,
  `user_id` varchar(16) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,
  `register_date` varchar(32) DEFAULT NULL,
  PRIMARY KEY (`origin_name`),
  KEY `origin_FK` (`user_id`),
  CONSTRAINT `origin_FK` FOREIGN KEY (`user_id`) REFERENCES `user` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `origin`
--

LOCK TABLES `origin` WRITE;
/*!40000 ALTER TABLE `origin` DISABLE KEYS */;
/*!40000 ALTER TABLE `origin` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `seller`
--

DROP TABLE IF EXISTS `seller`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `seller` (
  `seller_tag` int unsigned NOT NULL AUTO_INCREMENT,
  `registration_number` varchar(16) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,
  `registration_name` varchar(32) DEFAULT NULL,
  `seller_name` varchar(32) DEFAULT NULL,
  `representative` varchar(32) DEFAULT NULL,
  `description` varchar(128) DEFAULT NULL,
  `phone_number` varchar(16) DEFAULT NULL,
  `fax_number` varchar(16) DEFAULT NULL,
  `address` varchar(128) DEFAULT NULL,
  `business_status` varchar(32) DEFAULT NULL,
  `business_item` varchar(32) DEFAULT NULL,
  `coupon_dissount` float DEFAULT NULL,
  `card_discount` float DEFAULT NULL,
  `use_flag` tinyint unsigned DEFAULT NULL,
  `user_id` varchar(16) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,
  `register_date` varchar(32) DEFAULT NULL,
  PRIMARY KEY (`seller_tag`),
  KEY `seller_FK` (`user_id`),
  CONSTRAINT `seller_FK` FOREIGN KEY (`user_id`) REFERENCES `user` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `seller`
--

LOCK TABLES `seller` WRITE;
/*!40000 ALTER TABLE `seller` DISABLE KEYS */;
/*!40000 ALTER TABLE `seller` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `seller_cost`
--

DROP TABLE IF EXISTS `seller_cost`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `seller_cost` (
  `seller_cost_index` int unsigned NOT NULL AUTO_INCREMENT,
  `seller_tag` int unsigned DEFAULT NULL,
  `coupon_discount` float DEFAULT NULL,
  `card_discount` float DEFAULT NULL,
  `advertisement_cost` bigint unsigned DEFAULT NULL,
  `partner_levy` bigint unsigned DEFAULT NULL,
  `product_maintenance_cost` bigint unsigned DEFAULT NULL,
  `penalty_cost` bigint unsigned DEFAULT NULL,
  `delivery_cost` bigint unsigned DEFAULT NULL,
  `user_id` varchar(16) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,
  `register_date` varchar(32) DEFAULT NULL,
  PRIMARY KEY (`seller_cost_index`),
  KEY `seller_cost_FK_1` (`user_id`),
  KEY `seller_cost_FK` (`seller_tag`),
  CONSTRAINT `seller_cost_FK` FOREIGN KEY (`seller_tag`) REFERENCES `seller` (`seller_tag`),
  CONSTRAINT `seller_cost_FK_1` FOREIGN KEY (`user_id`) REFERENCES `user` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `seller_cost`
--

LOCK TABLES `seller_cost` WRITE;
/*!40000 ALTER TABLE `seller_cost` DISABLE KEYS */;
/*!40000 ALTER TABLE `seller_cost` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `seller_selling_type`
--

DROP TABLE IF EXISTS `seller_selling_type`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `seller_selling_type` (
  `seller_tag` int unsigned NOT NULL,
  `type` tinyint unsigned NOT NULL,
  `user_id` varchar(16) DEFAULT NULL,
  `register_date` varchar(32) DEFAULT NULL,
  PRIMARY KEY (`seller_tag`,`type`),
  KEY `seller_selling_type_FK_1` (`type`),
  KEY `seller_selling_type_FK_2` (`user_id`),
  CONSTRAINT `seller_selling_type_FK` FOREIGN KEY (`seller_tag`) REFERENCES `seller` (`seller_tag`),
  CONSTRAINT `seller_selling_type_FK_1` FOREIGN KEY (`type`) REFERENCES `selling_type` (`type`),
  CONSTRAINT `seller_selling_type_FK_2` FOREIGN KEY (`user_id`) REFERENCES `user` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `seller_selling_type`
--

LOCK TABLES `seller_selling_type` WRITE;
/*!40000 ALTER TABLE `seller_selling_type` DISABLE KEYS */;
/*!40000 ALTER TABLE `seller_selling_type` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `selling_type`
--

DROP TABLE IF EXISTS `selling_type`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `selling_type` (
  `type` tinyint unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(8) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,
  PRIMARY KEY (`type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `selling_type`
--

LOCK TABLES `selling_type` WRITE;
/*!40000 ALTER TABLE `selling_type` DISABLE KEYS */;
/*!40000 ALTER TABLE `selling_type` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `supplier`
--

DROP TABLE IF EXISTS `supplier`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `supplier` (
  `supplier_tag` int unsigned NOT NULL AUTO_INCREMENT,
  `suplier_name` varchar(32) DEFAULT NULL,
  `suplier_type` tinyint unsigned DEFAULT NULL COMMENT '1: 위탁, 2: 사입, 3: 직수입, 4: 미입고',
  `use_flag` tinyint unsigned DEFAULT NULL,
  `description` varchar(128) DEFAULT NULL,
  `user_id` varchar(16) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,
  `register_date` varchar(32) DEFAULT NULL,
  PRIMARY KEY (`supplier_tag`),
  KEY `supplier_FK` (`user_id`),
  CONSTRAINT `supplier_FK` FOREIGN KEY (`user_id`) REFERENCES `user` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `supplier`
--

LOCK TABLES `supplier` WRITE;
/*!40000 ALTER TABLE `supplier` DISABLE KEYS */;
/*!40000 ALTER TABLE `supplier` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `user`
--

DROP TABLE IF EXISTS `user`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `user` (
  `user_id` varchar(16) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `name` varchar(8) DEFAULT NULL,
  `password` varchar(512) DEFAULT NULL,
  `department` varchar(32) DEFAULT NULL,
  `phone_number` varchar(16) DEFAULT NULL,
  `email` varchar(32) DEFAULT NULL,
  `use_flag` tinyint unsigned DEFAULT NULL,
  `office_tag` int unsigned DEFAULT NULL,
  `register_date` varchar(32) DEFAULT NULL,
  PRIMARY KEY (`user_id`),
  KEY `user_FK` (`office_tag`),
  CONSTRAINT `user_FK` FOREIGN KEY (`office_tag`) REFERENCES `office` (`office_tag`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `user`
--

LOCK TABLES `user` WRITE;
/*!40000 ALTER TABLE `user` DISABLE KEYS */;
/*!40000 ALTER TABLE `user` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `user_authority`
--

DROP TABLE IF EXISTS `user_authority`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `user_authority` (
  `user_id` varchar(16) NOT NULL,
  `community_board_flag` tinyint unsigned DEFAULT NULL,
  `goods_management_flag` tinyint unsigned DEFAULT NULL,
  `consignment_management_flag` tinyint unsigned DEFAULT NULL,
  `move_management_flag` tinyint unsigned DEFAULT NULL,
  `sell_managemant_flag` tinyint unsigned DEFAULT NULL,
  `remain_management_flag` tinyint unsigned DEFAULT NULL,
  `sale_management_flag` tinyint unsigned DEFAULT NULL,
  `system_management_flag` tinyint unsigned DEFAULT NULL,
  `user_authority_management_flag` tinyint unsigned DEFAULT NULL,
  PRIMARY KEY (`user_id`),
  CONSTRAINT `user_authority_FK` FOREIGN KEY (`user_id`) REFERENCES `user` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `user_authority`
--

LOCK TABLES `user_authority` WRITE;
/*!40000 ALTER TABLE `user_authority` DISABLE KEYS */;
/*!40000 ALTER TABLE `user_authority` ENABLE KEYS */;
UNLOCK TABLES;
SET @@SESSION.SQL_LOG_BIN = @MYSQLDUMP_TEMP_LOG_BIN;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2022-11-17 10:54:22
