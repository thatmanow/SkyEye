-- ============ audit_logs ============
*************************** 1. row ***************************
audit_logs
CREATE TABLE `audit_logs` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` bigint DEFAULT NULL,
  `role` varchar(32) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `action` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '如 biz.graph.expand / admin.audit.approve',
  `resource` varchar(128) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '操作对象，如 company:12',
  `detail` text COLLATE utf8mb4_unicode_ci COMMENT '参数摘要 JSON',
  `ip_hash` varchar(32) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`id`),
  KEY `ix_audit_logs_user_id` (`user_id`),
  KEY `ix_audit_logs_created_at` (`created_at`)
) ENGINE=InnoDB AUTO_INCREMENT=61 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci

-- ============ collect_logs ============
*************************** 1. row ***************************
collect_logs
CREATE TABLE `collect_logs` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `source_code` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `task_type` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'import/crawl/sdk/sync',
  `params` text COLLATE utf8mb4_unicode_ci COMMENT '任务参数 JSON',
  `status` varchar(16) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'success/failed',
  `records` int NOT NULL COMMENT '本次处理记录数',
  `message` text COLLATE utf8mb4_unicode_ci,
  `operator_id` bigint DEFAULT NULL COMMENT '操作管理员（人工导入时）',
  `started_at` datetime DEFAULT NULL,
  `finished_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `ix_collect_logs_source_code` (`source_code`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci

-- ============ companies ============
*************************** 1. row ***************************
companies
CREATE TABLE `companies` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `name` varchar(256) COLLATE utf8mb4_unicode_ci NOT NULL,
  `short_name` varchar(128) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '常用简称',
  `credit_code` varchar(32) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '统一社会信用代码（演示库为 SEED- 前缀演示值）',
  `legal_person` varchar(128) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '法定代表人（公开工商信息）',
  `reg_status` varchar(32) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '存续/在业/注销/吊销/迁出',
  `reg_capital_wan` decimal(18,2) DEFAULT NULL COMMENT '注册资本（万元）',
  `paid_capital_wan` decimal(18,2) DEFAULT NULL COMMENT '实缴资本（万元）',
  `founded_date` date DEFAULT NULL,
  `company_type` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '有限责任公司/股份有限公司等',
  `industry` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `province` varchar(32) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `city` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `address` varchar(512) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `business_scope` text COLLATE utf8mb4_unicode_ci,
  `reg_authority` varchar(128) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '登记机关',
  `listed_code` varchar(12) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '证券代码（上市公司）',
  `employee_scale` varchar(32) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '人员规模档位：0-50/50-150/150-500/500-1000/1000+',
  `is_demo` tinyint(1) NOT NULL COMMENT '演示数据标记',
  `source` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '数据来源标识',
  `source_url` varchar(512) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '来源可溯源链接',
  `collected_at` datetime DEFAULT NULL COMMENT '采集时间',
  `created_at` datetime NOT NULL DEFAULT (now()),
  `updated_at` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`id`),
  UNIQUE KEY `credit_code` (`credit_code`),
  KEY `ix_companies_name` (`name`),
  KEY `ix_companies_industry` (`industry`),
  KEY `ix_companies_province` (`province`),
  KEY `ix_companies_city` (`city`),
  FULLTEXT KEY `ft_companies_search` (`name`,`business_scope`,`industry`) /*!50100 WITH PARSER `ngram` */ 
) ENGINE=InnoDB AUTO_INCREMENT=18 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci

-- ============ company_branches ============
*************************** 1. row ***************************
company_branches
CREATE TABLE `company_branches` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `company_id` bigint NOT NULL,
  `branch_name` varchar(256) COLLATE utf8mb4_unicode_ci NOT NULL,
  `branch_status` varchar(32) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `branch_person` varchar(128) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '分支机构负责人',
  `province` varchar(32) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `city` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `source` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `updated_at` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`id`),
  KEY `ix_company_branches_company_id` (`company_id`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci

-- ============ company_changes ============
*************************** 1. row ***************************
company_changes
CREATE TABLE `company_changes` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `company_id` bigint NOT NULL,
  `change_type` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '法定代表人变更/注册资本变更/股东变更/经营范围变更/注销备案等',
  `before_value` varchar(512) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `after_value` varchar(512) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `change_date` date DEFAULT NULL,
  `source` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`id`),
  KEY `ix_company_changes_change_date` (`change_date`),
  KEY `ix_company_changes_company_id` (`company_id`)
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci

-- ============ company_investments ============
*************************** 1. row ***************************
company_investments
CREATE TABLE `company_investments` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `investor_id` bigint NOT NULL COMMENT '投资方企业 ID',
  `investee_id` bigint DEFAULT NULL COMMENT '被投企业 ID（可能未入库）',
  `investee_name` varchar(256) COLLATE utf8mb4_unicode_ci NOT NULL,
  `investee_credit_code` varchar(32) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `share_ratio` decimal(8,4) DEFAULT NULL,
  `invested_amount_wan` decimal(18,2) DEFAULT NULL COMMENT '投资金额（万元）',
  `investee_reg_status` varchar(32) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `source` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `updated_at` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`id`),
  KEY `ix_company_investments_investee_id` (`investee_id`),
  KEY `ix_company_investments_investor_id` (`investor_id`)
) ENGINE=InnoDB AUTO_INCREMENT=14 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci

-- ============ company_personnel ============
*************************** 1. row ***************************
company_personnel
CREATE TABLE `company_personnel` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `company_id` bigint NOT NULL,
  `name` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL,
  `position` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '董事长/总经理/董事/监事等',
  `is_legal_person` tinyint(1) NOT NULL,
  `source` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `updated_at` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`id`),
  KEY `ix_company_personnel_company_id` (`company_id`)
) ENGINE=InnoDB AUTO_INCREMENT=11 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci

-- ============ company_shareholders ============
*************************** 1. row ***************************
company_shareholders
CREATE TABLE `company_shareholders` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `company_id` bigint NOT NULL,
  `holder_name` varchar(256) COLLATE utf8mb4_unicode_ci NOT NULL,
  `holder_type` varchar(16) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'person/company',
  `holder_credit_code` varchar(32) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '机构股东信用代码',
  `share_ratio` decimal(8,4) DEFAULT NULL COMMENT '持股比例(%)',
  `subscribed_capital_wan` decimal(18,2) DEFAULT NULL COMMENT '认缴出资（万元）',
  `source` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `updated_at` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`id`),
  KEY `ix_company_shareholders_company_id` (`company_id`)
) ENGINE=InnoDB AUTO_INCREMENT=15 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci

-- ============ complaints ============
*************************** 1. row ***************************
complaints
CREATE TABLE `complaints` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `subject_type` varchar(16) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'merchant/estate/landlord/agency/company',
  `subject_id` bigint NOT NULL COMMENT '关联主体ID；landlord/agency 无实体时为0',
  `subject_label` varchar(256) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '主体展示名（房东/中介为脱敏名）',
  `user_id` bigint DEFAULT NULL,
  `content` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `category` varchar(32) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '押金纠纷/虚假宣传/服务态度/质量等',
  `status` varchar(16) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '仅 approved 对外可见',
  `audit_reason` varchar(256) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `audited_by` bigint DEFAULT NULL,
  `audited_at` datetime DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`id`),
  KEY `ix_complaints_subject_type` (`subject_type`),
  KEY `ix_complaints_status` (`status`)
) ENGINE=InnoDB AUTO_INCREMENT=15 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci

-- ============ data_sources ============
*************************** 1. row ***************************
data_sources
CREATE TABLE `data_sources` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `code` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `name` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL,
  `type` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'official_web/official_sdk/ugc/seed/third_party_api',
  `url` varchar(512) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `license_note` text COLLATE utf8mb4_unicode_ci COMMENT '合法性说明',
  `enabled` tinyint(1) NOT NULL,
  `last_synced_at` datetime DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_source_code` (`code`)
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci

-- ============ housing_estates ============
*************************** 1. row ***************************
housing_estates
CREATE TABLE `housing_estates` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `name` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL,
  `city` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `district` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `address` varchar(512) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `developer` varchar(256) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '开发商（企业名，公开信息）',
  `property_company` varchar(256) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '物业公司',
  `build_year` int DEFAULT NULL,
  `complaint_count` int NOT NULL,
  `is_demo` tinyint(1) NOT NULL,
  `source` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT (now()),
  `updated_at` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`id`),
  KEY `ix_housing_estates_name` (`name`),
  KEY `ix_housing_estates_city` (`city`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci

-- ============ lead_favorites ============
*************************** 1. row ***************************
lead_favorites
CREATE TABLE `lead_favorites` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `lead_id` bigint NOT NULL,
  `user_id` bigint NOT NULL,
  `created_at` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_lead_fav` (`lead_id`,`user_id`),
  KEY `ix_lead_favorites_user_id` (`user_id`),
  KEY `ix_lead_favorites_lead_id` (`lead_id`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci

-- ============ lead_follows ============
*************************** 1. row ***************************
lead_follows
CREATE TABLE `lead_follows` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `lead_id` bigint NOT NULL,
  `user_id` bigint NOT NULL,
  `status` varchar(16) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'new/following/won/lost',
  `note` text COLLATE utf8mb4_unicode_ci,
  `next_action` varchar(256) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT (now()),
  `updated_at` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`id`),
  KEY `ix_lead_follows_lead_id` (`lead_id`),
  KEY `ix_lead_follows_user_id` (`user_id`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci

-- ============ leads ============
*************************** 1. row ***************************
leads
CREATE TABLE `leads` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `company_id` bigint NOT NULL,
  `company_name` varchar(256) COLLATE utf8mb4_unicode_ci NOT NULL,
  `industry` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `province` varchar(32) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `employee_scale` varchar(32) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `signal_type` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '线索信号：新注册/扩张/中标/融资/风险缓解等',
  `signal_desc` varchar(512) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `risk_delta` int NOT NULL COMMENT '风险分变化（正=恶化，负=改善）',
  `score` int NOT NULL COMMENT '线索价值分 0-100',
  `discovered_at` date DEFAULT NULL,
  `is_demo` tinyint(1) NOT NULL,
  `created_at` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`id`),
  KEY `ix_leads_province` (`province`),
  KEY `ix_leads_employee_scale` (`employee_scale`),
  KEY `ix_leads_industry` (`industry`)
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci

-- ============ merchant_reviews ============
*************************** 1. row ***************************
merchant_reviews
CREATE TABLE `merchant_reviews` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `merchant_id` bigint NOT NULL,
  `user_id` bigint NOT NULL,
  `rating` int NOT NULL COMMENT '1-5 星',
  `content` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `status` varchar(16) COLLATE utf8mb4_unicode_ci NOT NULL,
  `audit_reason` varchar(256) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `audited_by` bigint DEFAULT NULL,
  `audited_at` datetime DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`id`),
  KEY `ix_merchant_reviews_status` (`status`),
  KEY `ix_merchant_reviews_merchant_id` (`merchant_id`)
) ENGINE=InnoDB AUTO_INCREMENT=13 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci

-- ============ merchants ============
*************************** 1. row ***************************
merchants
CREATE TABLE `merchants` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `name` varchar(256) COLLATE utf8mb4_unicode_ci NOT NULL,
  `category` varchar(32) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '餐饮/零售/教培/美容/健身等',
  `address` varchar(512) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `city` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `credit_code` varchar(32) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '统一社会信用代码（演示值）',
  `reg_status` varchar(32) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `business_scope` text COLLATE utf8mb4_unicode_ci,
  `rating_avg` float NOT NULL COMMENT '评价聚合均分（仅统计过审评价）',
  `rating_count` int NOT NULL,
  `complaint_count` int NOT NULL COMMENT '过审投诉数',
  `is_demo` tinyint(1) NOT NULL,
  `source` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT (now()),
  `updated_at` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`id`),
  KEY `ix_merchants_name` (`name`),
  KEY `ix_merchants_city` (`city`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci

-- ============ monitor_schedules ============
*************************** 1. row ***************************
monitor_schedules
CREATE TABLE `monitor_schedules` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` bigint NOT NULL,
  `freq` varchar(16) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'daily/weekly',
  `scope` varchar(16) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'watched=关注企业/all=全部监控',
  `enabled` tinyint(1) NOT NULL,
  `last_run_at` datetime DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT (now()),
  `updated_at` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`id`),
  KEY `ix_monitor_schedules_user_id` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci

-- ============ notifications ============
*************************** 1. row ***************************
notifications
CREATE TABLE `notifications` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` bigint NOT NULL,
  `type` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'monitor/report/audit/system',
  `title` varchar(256) COLLATE utf8mb4_unicode_ci NOT NULL,
  `content` text COLLATE utf8mb4_unicode_ci,
  `ref_url` varchar(256) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `is_read` tinyint(1) NOT NULL,
  `created_at` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`id`),
  KEY `ix_notifications_user_id` (`user_id`),
  KEY `ix_notifications_is_read` (`is_read`)
) ENGINE=InnoDB AUTO_INCREMENT=26 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci

-- ============ post_comments ============
*************************** 1. row ***************************
post_comments
CREATE TABLE `post_comments` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `post_id` bigint NOT NULL,
  `user_id` bigint NOT NULL,
  `content` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `is_anonymous` tinyint(1) NOT NULL,
  `status` varchar(16) COLLATE utf8mb4_unicode_ci NOT NULL,
  `audit_reason` varchar(256) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `audited_by` bigint DEFAULT NULL,
  `audited_at` datetime DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`id`),
  KEY `ix_post_comments_status` (`status`),
  KEY `ix_post_comments_post_id` (`post_id`)
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci

-- ============ post_likes ============
*************************** 1. row ***************************
post_likes
CREATE TABLE `post_likes` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `post_id` bigint NOT NULL,
  `user_id` bigint NOT NULL,
  `created_at` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_post_like` (`post_id`,`user_id`),
  KEY `ix_post_likes_post_id` (`post_id`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci

-- ============ posts ============
*************************** 1. row ***************************
posts
CREATE TABLE `posts` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` bigint NOT NULL,
  `category` varchar(16) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'avoid_pit避雷/recommend推荐',
  `title` varchar(256) COLLATE utf8mb4_unicode_ci NOT NULL,
  `content` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `is_anonymous` tinyint(1) NOT NULL,
  `status` varchar(16) COLLATE utf8mb4_unicode_ci NOT NULL,
  `audit_reason` varchar(256) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `audited_by` bigint DEFAULT NULL,
  `audited_at` datetime DEFAULT NULL,
  `like_count` int NOT NULL,
  `comment_count` int NOT NULL,
  `created_at` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`id`),
  KEY `ix_posts_created_at` (`created_at`),
  KEY `ix_posts_status` (`status`)
) ENGINE=InnoDB AUTO_INCREMENT=10 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci

-- ============ report_records ============
*************************** 1. row ***************************
report_records
CREATE TABLE `report_records` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `target_type` varchar(16) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'post/comment/review/complaint',
  `target_id` bigint NOT NULL,
  `reporter_id` bigint DEFAULT NULL,
  `reporter_ip_hash` varchar(32) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `reason` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `description` text COLLATE utf8mb4_unicode_ci,
  `status` varchar(16) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'pending/handled/dismissed',
  `handled_by` bigint DEFAULT NULL,
  `handle_result` varchar(256) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `handled_at` datetime DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`id`),
  KEY `ix_report_records_status` (`status`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci

-- ============ report_tasks ============
*************************** 1. row ***************************
report_tasks
CREATE TABLE `report_tasks` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` bigint NOT NULL,
  `company_id` bigint NOT NULL,
  `company_name` varchar(256) COLLATE utf8mb4_unicode_ci NOT NULL,
  `template` varchar(16) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'standard/deep',
  `status` varchar(16) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'queued/running/done/failed',
  `progress` int NOT NULL COMMENT '0-100',
  `file_pdf` varchar(512) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `file_xlsx` varchar(512) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `error` text COLLATE utf8mb4_unicode_ci,
  `params` text COLLATE utf8mb4_unicode_ci COMMENT '生成参数 JSON',
  `created_at` datetime NOT NULL DEFAULT (now()),
  `finished_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `ix_report_tasks_status` (`status`),
  KEY `ix_report_tasks_created_at` (`created_at`),
  KEY `ix_report_tasks_user_id` (`user_id`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci

-- ============ risk_records ============
*************************** 1. row ***************************
risk_records
CREATE TABLE `risk_records` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `subject_type` varchar(16) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'company/person',
  `subject_id` bigint NOT NULL COMMENT '企业ID；个人固定0',
  `subject_name` varchar(256) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '企业名 或 个人脱敏名',
  `risk_type` varchar(16) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'judicial/business/finance/public_opinion/admin_penalty',
  `risk_subtype` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '如 买卖合同纠纷/欠税公告/被执行人/失信被执行人',
  `title` varchar(512) COLLATE utf8mb4_unicode_ci NOT NULL,
  `content_digest` text COLLATE utf8mb4_unicode_ci COMMENT '摘要（脱敏后）',
  `amount_wan` decimal(18,2) DEFAULT NULL COMMENT '涉案/执行金额（万元）',
  `court` varchar(128) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '审理法院',
  `case_no` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '案号（脱敏）',
  `risk_level` varchar(8) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'low/medium/high',
  `occur_date` date DEFAULT NULL,
  `publish_date` date DEFAULT NULL,
  `source` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '数据来源标识（可溯源）',
  `source_url` varchar(512) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `is_demo` tinyint(1) NOT NULL,
  `created_at` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`id`),
  KEY `idx_risk_type_date` (`risk_type`,`occur_date`),
  KEY `idx_risk_subject` (`subject_type`,`subject_id`)
) ENGINE=InnoDB AUTO_INCREMENT=18 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci

-- ============ users ============
*************************** 1. row ***************************
users
CREATE TABLE `users` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `account` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '账号（手机号或邮箱明文唯一索引；手机/邮箱另有密文列）',
  `nickname` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,
  `password_hash` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'bcrypt',
  `role` enum('user','premium','enterprise_admin','platform_admin') COLLATE utf8mb4_unicode_ci NOT NULL,
  `phone_enc` varchar(256) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '手机号 AES-GCM 密文',
  `email_enc` varchar(256) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '邮箱 AES-GCM 密文',
  `status` enum('normal','banned') COLLATE utf8mb4_unicode_ci NOT NULL,
  `vip_expire_at` datetime DEFAULT NULL COMMENT '高级会员到期时间',
  `last_login_at` datetime DEFAULT NULL,
  `last_login_ip_hash` varchar(32) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '登录 IP 哈希（不留明文）',
  `created_at` datetime NOT NULL DEFAULT (now()),
  `updated_at` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`id`),
  UNIQUE KEY `account` (`account`)
) ENGINE=InnoDB AUTO_INCREMENT=10 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci

-- ============ watch_events ============
*************************** 1. row ***************************
watch_events
CREATE TABLE `watch_events` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `company_id` bigint NOT NULL,
  `company_name` varchar(256) COLLATE utf8mb4_unicode_ci NOT NULL,
  `event_type` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'change/risk',
  `event_ref_id` bigint DEFAULT NULL COMMENT '关联 company_changes/risk_records 的 id',
  `title` varchar(512) COLLATE utf8mb4_unicode_ci NOT NULL,
  `detail` text COLLATE utf8mb4_unicode_ci,
  `risk_level` varchar(8) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'info/low/medium/high',
  `occurred_at` datetime DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`id`),
  KEY `ix_watch_events_occurred_at` (`occurred_at`),
  KEY `ix_watch_events_company_id` (`company_id`)
) ENGINE=InnoDB AUTO_INCREMENT=15 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci

-- ============ watch_items ============
*************************** 1. row ***************************
watch_items
CREATE TABLE `watch_items` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` bigint NOT NULL,
  `company_id` bigint NOT NULL,
  `company_name` varchar(256) COLLATE utf8mb4_unicode_ci NOT NULL,
  `enabled` tinyint(1) NOT NULL,
  `created_at` datetime NOT NULL DEFAULT (now()),
  `updated_at` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_watch` (`user_id`,`company_id`),
  KEY `ix_watch_items_user_id` (`user_id`),
  KEY `ix_watch_items_company_id` (`company_id`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci

