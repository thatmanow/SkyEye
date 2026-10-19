<template>
  <div class="page wide">
    <h1 class="page-title">平台管理</h1>
    <p class="page-sub">内容审核 · 用户管理 · 数据维护 · 审计留痕 · 运营看板</p>

    <el-tabs v-model="tab" class="tyt-card" @tab-change="onTab">
      <!-- 看板 -->
      <el-tab-pane label="运营看板" name="dashboard">
        <div class="stat-cards" v-if="dash">
          <div class="stat"><div class="s-num">{{ dash.stats.total_companies }}</div><div class="s-label">企业总数</div></div>
          <div class="stat"><div class="s-num">{{ dash.stats.total_users }}</div><div class="s-label">用户总数</div></div>
          <div class="stat"><div class="s-num">{{ dash.stats.total_risks }}</div><div class="s-label">风险记录</div></div>
          <div class="stat"><div class="s-num">{{ dash.stats.total_leads }}</div><div class="s-label">商机线索</div></div>
          <div class="stat warn"><div class="s-num">{{ pendingTotal }}</div><div class="s-label">待审内容</div></div>
        </div>
        <div class="charts" v-if="dash">
          <div ref="riskChartEl" class="chart-box"></div>
          <div ref="roleChartEl" class="chart-box"></div>
        </div>
      </el-tab-pane>

      <!-- 审核 -->
      <el-tab-pane label="内容审核" name="audit">
        <div class="audit-tabs">
          <el-radio-group v-model="auditType" @change="resetPending">
            <el-radio-button v-for="(label, key) in auditTypes" :key="key" :value="key">{{ label }}</el-radio-button>
          </el-radio-group>
          <div class="audit-ops">
            <el-button size="small" :loading="scanning" @click="doScan">🔍 违规扫描</el-button>
            <el-button size="small" @click="openWordsDialog">📋 违规标准</el-button>
          </div>
        </div>
        <div class="scan-result" v-if="scanResult">
          <span class="scan-summary">
            违规扫描完成：待审 {{ scanResult.total_pending }} 条，命中违规 <b>{{ scanResult.total_hit }}</b> 条
          </span>
          <span class="scan-detail text-dim">
            <template v-for="(s, k) in scanResult.stats" :key="k">
              {{ s.type_name }} {{ s.hit }}/{{ s.pending }} ·
            </template>
          </span>
          <button class="scan-close" @click="scanResult = null">关闭</button>
        </div>
        <el-empty v-if="!pendingItems.length" description="该类型暂无待审内容" />
        <div v-for="p in pendingItems" :key="p.id" class="p-item" :class="{ 'p-violation': p.violations?.length }">
          <div class="p-head">
            <el-tag size="small" effect="dark" type="warning">ID {{ p.id }}</el-tag>
            <el-tag v-if="auditType === 'comment' && p.post_id" size="small" effect="plain">帖子 #{{ p.post_id }}</el-tag>
            <el-tag v-if="auditType === 'review'" size="small" effect="plain" type="warning">
              ⭐ {{ p.rating }} · {{ p.merchant_name }}
            </el-tag>
            <el-tag v-if="auditType === 'complaint'" size="small" effect="plain" type="info">
              {{ p.subject_label }} · {{ p.category }}
            </el-tag>
            <span class="p-title">{{ p.title || p.content?.slice(0, 40) }}</span>
            <span class="p-date text-dim">{{ p.created_at }}</span>
          </div>
          <p class="p-content">{{ p.content }}</p>
          <div v-if="p.images?.length" class="p-imgs">
            <el-image v-for="(img, i) in p.images" :key="img" class="p-img" :src="img" fit="cover"
                      :alt="`帖子配图${i + 1}`" :preview-src-list="p.images" :preview-teleported="true" loading="lazy" />
          </div>
          <div class="p-violation-warn" v-if="p.violations?.length">
            ⚠ 检测到可能违规的词语: {{ p.violations.join(', ') }}
          </div>
          <div class="p-actions">
            <el-button size="small" type="success" @click="audit(p, 'approve')">通过</el-button>
            <el-button size="small" type="danger" plain @click="audit(p, 'reject')">拒绝</el-button>
          </div>
        </div>
        <div class="pager" v-if="auditListTotal > 10">
          <el-pagination background layout="prev, pager, next" :total="auditListTotal" :page-size="10"
                         :current-page="pendingPage" @current-change="loadPending" />
        </div>
      </el-tab-pane>

      <!-- 用户 -->
      <el-tab-pane label="用户管理" name="users">
        <div class="user-filter">
          <el-input v-model="userKw" placeholder="昵称 / 账号" clearable style="width: 220px" @keyup.enter="resetUsers" />
          <el-select v-model="userRole" placeholder="角色" clearable style="width: 150px" @change="resetUsers">
            <el-option label="普通用户" value="user" />
            <el-option label="高级会员" value="premium" />
            <el-option label="企业管理员" value="enterprise_admin" />
            <el-option label="平台管理员" value="platform_admin" />
          </el-select>
          <el-button @click="resetUsers">查询</el-button>
          <span class="user-total text-dim">共 {{ userTotal }} 位用户</span>
        </div>
        <el-table :data="users" size="small">
          <el-table-column prop="id" label="ID" width="60" />
          <el-table-column prop="nickname" label="昵称" width="130" />
          <el-table-column prop="account" label="账号" min-width="180" />
          <el-table-column label="角色" width="130">
            <template #default="{ row }">
              <el-select :model-value="row.role" size="small" @change="(v: any) => changeRole(row, v)">
                <el-option label="普通用户" value="user" />
                <el-option label="高级会员" value="premium" />
                <el-option label="企业管理员" value="enterprise_admin" />
                <el-option label="平台管理员" value="platform_admin" />
              </el-select>
            </template>
          </el-table-column>
          <el-table-column label="状态" width="90">
            <template #default="{ row }">
              <el-tag :type="row.status === 'normal' ? 'success' : 'danger'" size="small" effect="dark">
                {{ row.status === 'normal' ? '正常' : '封禁' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="created_at" label="注册时间" width="170" />
          <el-table-column label="操作" width="90">
            <template #default="{ row }">
              <el-button size="small" :type="row.status === 'normal' ? 'danger' : 'success'" plain
                         @click="toggleStatus(row)">
                {{ row.status === 'normal' ? '封禁' : '解封' }}
              </el-button>
            </template>
          </el-table-column>
        </el-table>
        <div class="pager" v-if="userTotal > 10">
          <el-pagination background layout="prev, pager, next" :total="userTotal" :page-size="10"
                         :current-page="userPage" @current-change="loadUsers" />
        </div>
      </el-tab-pane>

      <!-- 数据维护 -->
      <el-tab-pane label="数据维护" name="data">
        <h4>已登记数据源（合法来源白名单）</h4>
        <el-table :data="pagedSources" size="small">
          <el-table-column prop="code" label="标识" width="110" />
          <el-table-column prop="name" label="名称" min-width="200" />
          <el-table-column prop="type" label="类型" width="120" />
          <el-table-column label="链接">
            <template #default="{ row }">
              <a :href="row.url" target="_blank" rel="noopener" class="mono">{{ row.url }}</a>
            </template>
          </el-table-column>
        </el-table>
        <div class="pager" v-if="sourcesTotal > 10">
          <el-pagination small background layout="prev, pager, next" :total="sourcesTotal" :page-size="10"
                         :current-page="srcPage" @current-change="(p: number) => srcPage = p" />
        </div>

        <h4>人工导入数据（CSV，写入采集留痕）</h4>
        <div class="import-form">
          <el-select v-model="importForm.source_code" style="width: 220px">
            <el-option v-for="s in sources" :key="s.code" :label="s.name" :value="s.code" />
          </el-select>
          <el-select v-model="importForm.entity" style="width: 180px">
            <el-option label="企业 (companies)" value="companies" />
            <el-option label="风险 (risks)" value="risks" />
            <el-option label="人员 (personnel)" value="personnel" />
            <el-option label="股东 (shareholders)" value="shareholders" />
          </el-select>
          <el-button type="primary" :loading="importing" @click="doImport"
                     style="background:linear-gradient(135deg,#6366f1,#8b5cf6);border:none">导入</el-button>
        </div>
        <el-input v-model="importForm.csv_content" type="textarea" :rows="5" class="csv-input"
                  placeholder="CSV 内容，首行为表头。示例：&#10;name,city,reg_status&#10;某某科技有限公司,上海,存续" />

        <h4>采集日志</h4>
        <el-table :data="collectLogs" size="small">
          <el-table-column prop="id" label="ID" width="70" />
          <el-table-column prop="task_type" label="类型" width="100" />
          <el-table-column prop="source_code" label="来源" width="120" />
          <el-table-column prop="summary" label="摘要" min-width="220" />
          <el-table-column prop="created_at" label="时间" width="170" />
        </el-table>
        <div class="pager" v-if="collectTotal > 10">
          <el-pagination background layout="prev, pager, next" :total="collectTotal" :page-size="10"
                         :current-page="collectPage" @current-change="loadCollectLogs" />
        </div>
      </el-tab-pane>

      <!-- AI 知识库 -->
      <el-tab-pane label="知识库" name="kb">
        <div class="kb-head">
          <div class="kb-stat-pills" v-if="kbStats">
            <span class="kb-pill total">📚 文档总数 {{ kbStats.total }}</span>
            <span class="kb-pill" v-for="(cnt, k) in kbStats.by_kind" :key="k">
              {{ kindName(String(k)) }} {{ cnt }}
            </span>
            <span class="kb-pill sync">同步状态：{{ syncStateText }}</span>
          </div>
          <div class="kb-actions">
            <el-button size="small" @click="kbAddVisible = true">＋ 手动录入</el-button>
            <el-button size="small" :loading="kbDocImporting" @click="kbImportVisible = true">📥 导入文档</el-button>
            <el-button size="small" type="primary" :loading="kbResyncing" @click="doKbResync"
                       style="background:linear-gradient(135deg,#6366f1,#8b5cf6);border:none">重新同步爬虫知识</el-button>
          </div>
        </div>

        <div class="kb-filter">
          <el-select v-model="kbKind" style="width: 170px" @change="loadKb(1)">
            <el-option label="全部类型" value="" />
            <el-option label="人民网资讯" value="people_article" />
            <el-option label="baostock 行情" value="baostock_quote" />
            <el-option label="手动录入" value="manual" />
          </el-select>
          <el-input v-model="kbKeyword" placeholder="搜索标题 / 正文关键词" style="width: 260px" clearable
                    @keyup.enter="loadKb(1)" @clear="loadKb(1)" />
          <el-button @click="loadKb(1)">搜索</el-button>
        </div>

        <el-table :data="kbDocs" size="small">
          <el-table-column label="类型" width="120">
            <template #default="{ row }">
              <el-tag size="small" :type="kbTagType(row.kind)" effect="plain">{{ row.kind_name }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="title" label="标题" min-width="220" show-overflow-tooltip />
          <el-table-column prop="source" label="来源" width="170" show-overflow-tooltip />
          <el-table-column label="原文链接" width="90">
            <template #default="{ row }">
              <a v-if="row.url" :href="row.url" target="_blank" rel="noopener">查看</a>
              <span v-else class="text-dim">--</span>
            </template>
          </el-table-column>
          <el-table-column label="内容摘录" min-width="260">
            <template #default="{ row }">
              <span class="kb-excerpt">{{ row.excerpt }}…</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="80">
            <template #default="{ row }">
              <el-button size="small" text type="danger" @click="delKbDoc(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
        <div class="pager" v-if="kbTotal > 10">
          <el-pagination background layout="prev, pager, next" :total="kbTotal" :page-size="10"
                         :current-page="kbPage" @current-change="loadKb" />
        </div>
      </el-tab-pane>

      <!-- 模型管理 -->
      <el-tab-pane label="模型管理" name="models">
        <!-- AI 问答模型 -->
        <div class="model-banner" v-if="modelCfg">
          <div class="mb-left">
            <div class="mb-title">百炼大模型开关<span class="mb-sub text-dim">AI 问答 · qwen-plus</span></div>
            <div class="mb-desc text-dim">{{ modelCfg.rule }}</div>
          </div>
          <div class="mb-switch">
            <span class="mb-state" :class="{ on: modelCfg.bailian_enabled }">
              {{ modelCfg.bailian_enabled ? '已开启' : '已关闭' }}
            </span>
            <el-switch v-model="modelCfg.bailian_enabled" :loading="bailianToggling"
                       @change="(v: boolean) => toggleBailianField('bailian_enabled', v)" />
          </div>
        </div>
        <div class="model-cards" v-if="modelCfg">
          <div class="model-card" v-for="(m, key) in modelCfg.models" :key="key"
               :class="{ 'mc-bailian': String(key) === 'bailian' }">
            <div class="mc-head">
              <span class="mc-title">{{ m.title }}</span>
              <el-tag size="small" :type="String(key) === 'bailian' ? 'warning' : 'success'" effect="dark">
                {{ String(key) === 'bailian' ? '云端' : '本地' }}
              </el-tag>
            </div>
            <p class="mc-intro">{{ m.intro }}</p>
            <ul class="mc-list">
              <li v-for="p in m.pros" :key="p">✅ {{ p }}</li>
              <li v-for="c in m.cons" :key="c" class="mc-con">⚠️ {{ c }}</li>
            </ul>
            <div class="mc-scope text-dim">🎯 生效范围：{{ m.apply_scope }}</div>
            <div class="mc-meta text-dim">引擎：{{ m.name }} · {{ m.provider }}</div>
          </div>
        </div>

        <!-- AI 识图模型 -->
        <div class="model-banner" v-if="modelCfg" style="margin-top: 16px">
          <div class="mb-left">
            <div class="mb-title">百炼识图模型开关<span class="mb-sub text-dim">AI 识图 · qwen-vl-ocr</span></div>
            <div class="mb-desc text-dim">{{ modelCfg.vision_rule }}</div>
          </div>
          <div class="mb-switch">
            <span class="mb-state" :class="{ on: modelCfg.bailian_vision_enabled }">
              {{ modelCfg.bailian_vision_enabled ? '已开启' : '已关闭' }}
            </span>
            <el-switch v-model="modelCfg.bailian_vision_enabled" :loading="bailianToggling"
                       @change="(v: boolean) => toggleBailianField('bailian_vision_enabled', v)" />
          </div>
        </div>
        <div class="model-cards" v-if="modelCfg">
          <div class="model-card" v-for="(m, key) in modelCfg.vision_models" :key="key"
               :class="{ 'mc-bailian': String(key) === 'bailian_vision' }">
            <div class="mc-head">
              <span class="mc-title">{{ m.title }}</span>
              <el-tag size="small" :type="String(key) === 'bailian_vision' ? 'warning' : 'success'" effect="dark">
                {{ String(key) === 'bailian_vision' ? '云端' : '本地' }}
              </el-tag>
            </div>
            <p class="mc-intro">{{ m.intro }}</p>
            <ul class="mc-list">
              <li v-for="p in m.pros" :key="p">✅ {{ p }}</li>
              <li v-for="c in m.cons" :key="c" class="mc-con">⚠️ {{ c }}</li>
            </ul>
            <div class="mc-scope text-dim">🎯 生效范围：{{ m.apply_scope }}</div>
            <div class="mc-meta text-dim">引擎：{{ m.name }} · {{ m.provider }}</div>
          </div>
        </div>
        <el-skeleton :rows="5" animated v-if="!modelCfg" />
      </el-tab-pane>

      <!-- 审计日志 -->
      <el-tab-pane label="审计日志" name="logs">
        <el-table :data="auditLogs" size="small">
          <el-table-column prop="id" label="ID" width="70" />
          <el-table-column prop="user_id" label="用户" width="80" />
          <el-table-column prop="action" label="动作" width="180" />
          <el-table-column prop="resource" label="对象" width="150" />
          <el-table-column label="详情" min-width="240">
            <template #default="{ row }">
              <span class="mono detail-json">{{ row.detail }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="created_at" label="时间" width="170" />
        </el-table>
        <div class="pager" v-if="logTotal > 10">
          <el-pagination background layout="prev, pager, next" :total="logTotal" :page-size="10"
                         :current-page="logPage" @current-change="loadLogs" />
        </div>
      </el-tab-pane>
    </el-tabs>

    <el-dialog v-model="kbAddVisible" title="手动录入知识文档" width="560px">
      <el-form label-position="top">
        <el-form-item label="标题（检索引用时展示）" required>
          <el-input v-model="kbAddForm.title" maxlength="120" placeholder="如：平台使用常见问题解答" />
        </el-form-item>
        <el-form-item label="参考链接（可选，AI 回答来源可跳转）">
          <el-input v-model="kbAddForm.url" maxlength="500" placeholder="https://…" />
        </el-form-item>
        <el-form-item label="正文内容（将向量化供 AI 检索）" required>
          <el-input v-model="kbAddForm.content" type="textarea" :rows="7" maxlength="8000" show-word-limit
                    placeholder="输入知识正文，建议 100 字以上，表述清晰完整" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="kbAddVisible = false">取消</el-button>
        <el-button type="primary" :loading="kbAdding" @click="doKbAdd"
                   style="background:linear-gradient(135deg,#6366f1,#8b5cf6);border:none">入库</el-button>
      </template>
    </el-dialog>

    <!-- 导入文档：自动提取文本切分入库（支持拖拽） -->
    <el-dialog v-model="kbImportVisible" title="导入文档到知识库" width="560px">
      <p class="text-dim" style="margin-top:0">
        支持 txt / md / csv / docx / pdf / xlsx / html，可直接把文件<strong>拖入下方区域</strong>或点击选择；
        服务端自动识别文本并按语义切分入库；导入的知识标记为「手动录入」，不参与每日爬虫清理，长期保留。
      </p>
      <el-form label-position="top">
        <el-form-item label="标题（留空则自动识别首行 / 文件名）">
          <el-input v-model="kbImportForm.title" maxlength="120" placeholder="如：公司风险排查操作手册" />
        </el-form-item>
        <el-form-item label="文档（拖入或点击选择）">
          <div
            class="kb-dropzone"
            :class="{ 'is-dragover': kbDragOver, 'has-file': !!kbImportFile }"
            @dragover.prevent="onKbDragOver"
            @dragenter.prevent="onKbDragOver"
            @dragleave.prevent="onKbDragLeave"
            @drop.prevent="onKbDrop"
            @click="triggerKbFileInput"
          >
            <template v-if="!kbImportFile">
              <div class="dz-icon">📥</div>
              <div class="dz-main">将文件拖到此处，或<span class="dz-link">点击选择</span></div>
              <div class="dz-sub text-dim">支持 txt / md / csv / docx / pdf / xlsx / html（≤ 20MB）</div>
            </template>
            <template v-else>
              <div class="dz-file">
                <span class="dz-file-icon">📄</span>
                <span class="dz-file-name">{{ kbImportFile.name }}</span>
                <span class="text-dim">（{{ (kbImportFile.size / 1024).toFixed(1) }} KB）</span>
                <el-button
                  size="small" text type="danger"
                  @click.stop="clearKbImportFile"
                >移除</el-button>
              </div>
            </template>
            <input
              ref="kbFileInput"
              type="file"
              class="kb-file-input"
              accept=".txt,.md,.csv,.docx,.pdf,.xlsx,.xls,.html,.htm"
              @change="onKbFileChange"
            />
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="kbImportVisible = false">取消</el-button>
        <el-button type="primary" :loading="kbDocImporting" @click="doKbImport"
                   style="background:linear-gradient(135deg,#6366f1,#8b5cf6);border:none">导入</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="wordsVisible" title="违规标准（内容审核自动识别词库）" width="640px">
      <p class="words-tip text-dim">
        参考第一版违规标准：从下方预设词库勾选启用，或手动添加自定义词；保存后立即生效，待审内容加载时自动识别命中词并标红提示。
      </p>

      <!-- 预设标准：按第一版分类分组勾选 -->
      <div class="vw-section">
        <div class="vw-section-title">预设标准（第一版词库分类）</div>
        <div class="vw-groups">
          <div v-for="g in presetGroups" :key="g.category" class="vw-group">
            <el-checkbox class="vw-group-check" :model-value="groupChecked(g)"
                         @change="(v: any) => togglePresetGroup(g, v)">{{ g.category }}</el-checkbox>
            <div class="vw-group-words">
              <el-checkbox v-for="w in g.words" :key="w" :model-value="activeWordSet.has(w)"
                           :label="w" @change="(v: any) => togglePreset(w, v)" />
            </div>
          </div>
        </div>
      </div>

      <!-- 手动添加：参考第一版「输入违规词 + 分类」 -->
      <div class="vw-section">
        <div class="vw-section-title">手动添加</div>
        <div class="vw-add-row">
          <el-input v-model="newWord" maxlength="64" placeholder="输入违规词"
                    @keyup.enter="addManualWord" />
          <el-select v-model="newWordCategory" style="width: 130px">
            <el-option v-for="c in vwCategories" :key="c" :label="c" :value="c" />
          </el-select>
          <el-button type="primary" plain @click="addManualWord">＋ 添加</el-button>
        </div>
      </div>

      <!-- 当前标准：词(分类) chips，可删除 -->
      <div class="vw-section">
        <div class="vw-section-title">当前标准 <span class="text-dim">（{{ wordsCount }} 个词，保存后生效）</span></div>
        <div class="vw-active">
          <el-empty v-if="!activeItems.length" description="尚未选择任何标准" :image-size="50" />
          <span v-for="i in activeItems" :key="i.word" class="vw-chip"
                :class="{ 'vw-chip-custom': !i.preset }">
            {{ i.word }}<em>{{ i.category }}</em>
            <i class="vw-chip-del" title="移除" @click="removeWordItem(i.word)">×</i>
          </span>
        </div>
      </div>

      <template #footer>
        <el-button @click="wordsVisible = false">取消</el-button>
        <el-button type="primary" :loading="savingWords" @click="saveWords"
                   style="background:linear-gradient(135deg,#6366f1,#8b5cf6);border:none">保存标准</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import * as echarts from 'echarts'
import { ElMessage } from 'element-plus'
import { adminApi } from '@/api/modules'
import { usePager } from '@/composables/usePager'

const tab = ref('dashboard')
const dash = ref<any>(null)

const auditType = ref('post')
const auditTypes: Record<string, string> = {
  post: '帖子', comment: '帖子评论', review: '商家评价', complaint: '投诉', report: '举报',
}
const pendingItems = ref<any[]>([])
const pendingPage = ref(1)
const auditListTotal = ref(0)

const users = ref<any[]>([])
const userKw = ref('')
const userRole = ref('')
const userTotal = ref(0)
const userPage = ref(1)

const sources = ref<any[]>([])
const collectLogs = ref<any[]>([])
const collectTotal = ref(0)
const collectPage = ref(1)
const auditLogs = ref<any[]>([])
const logTotal = ref(0)
const logPage = ref(1)

const { page: srcPage, total: sourcesTotal, paged: pagedSources } = usePager(sources)

const importForm = reactive({ source_code: 'gsxt', entity: 'companies', csv_content: '' })
const importing = ref(false)

const riskChartEl = ref<HTMLElement>()
const roleChartEl = ref<HTMLElement>()
let riskChart: echarts.ECharts | null = null
let roleChart: echarts.ECharts | null = null

const pendingTotal = computed(() => {
  const s = dash.value?.stats || {}
  return (s.pending_posts || 0) + (s.pending_reviews || 0) + (s.pending_complaints || 0)
    + (s.pending_abuse_reports || 0) + (s.pending_comments || 0)
})

async function loadDash() {
  dash.value = await adminApi.dashboard()
  await nextTick()
  renderCharts()
}

function renderCharts() {
  if (!dash.value) return
  const riskNameMap: Record<string, string> = {
    judicial: '司法', business: '经营', finance: '财务', public_opinion: '舆情', admin_penalty: '行政处罚',
  }
  if (riskChartEl.value) {
    riskChart?.dispose()
    riskChart = echarts.init(riskChartEl.value)
    riskChart.setOption({
      title: { text: '风险类型分布', textStyle: { color: '#0f172a', fontSize: 13 }, left: 'center' },
      tooltip: { trigger: 'item' },
      series: [{
        type: 'pie', radius: ['38%', '64%'],
        data: Object.entries(dash.value.risk_dist || {}).map(([k, v]) => ({
          name: riskNameMap[k] || k, value: v,
        })),
        label: { color: '#475569', fontSize: 11 },
        itemStyle: { borderColor: '#ffffff', borderWidth: 2 },
      }],
    })
  }
  if (roleChartEl.value) {
    roleChart?.dispose()
    roleChart = echarts.init(roleChartEl.value)
    roleChart.setOption({
      title: { text: '用户角色分布', textStyle: { color: '#0f172a', fontSize: 13 }, left: 'center' },
      tooltip: { trigger: 'axis' },
      grid: { left: 60, right: 20, top: 40, bottom: 30 },
      xAxis: { type: 'category', data: Object.keys(dash.value.role_dist || {}).map((k) => roleName(k)),
        axisLabel: { color: '#475569', fontSize: 11 } },
      yAxis: { type: 'value', axisLabel: { color: '#475569' }, splitLine: { lineStyle: { color: '#e2e8f0' } } },
      series: [{ type: 'bar', barWidth: 40, data: Object.values(dash.value.role_dist || {}),
        itemStyle: { color: '#6366f1', borderRadius: [4, 4, 0, 0] } }],
    })
  }
}

function roleName(r: string) {
  return ({ user: '普通用户', premium: '高级会员', enterprise_admin: '企业管理员', platform_admin: '平台管理员' } as any)[r] || r
}

async function loadPending(p = pendingPage.value) {
  pendingPage.value = p
  const data = await adminApi.pendingList(auditType.value, { page: p, page_size: 10 })
  pendingItems.value = data.items || []
  auditListTotal.value = data.total ?? pendingItems.value.length
}

/* ===== 违规标准与违规扫描（第一版自动识别逻辑 + 第一版分类词库） ===== */
const scanResult = ref<any>(null)
const scanning = ref(false)
const wordsVisible = ref(false)
const savingWords = ref(false)
/* 预设标准（第一版词库分类体系）与当前启用词条（词 + 分类） */
const presetGroups = ref<{ category: string; words: string[] }[]>([])
const vwCategories = ref<string[]>([])
const activeItems = ref<{ word: string; category: string; preset: boolean }[]>([])
const newWord = ref('')
const newWordCategory = ref('通用')

const activeWordSet = computed(() => new Set(activeItems.value.map((i) => i.word)))
const wordsCount = computed(() => activeItems.value.length)
const presetLookup = computed(() => {
  const m: Record<string, string> = {}
  for (const g of presetGroups.value) for (const w of g.words) m[w] = g.category
  return m
})

function togglePreset(word: string, checked: boolean | string | number) {
  if (checked) {
    activeItems.value.push({ word, category: presetLookup.value[word] || '通用', preset: true })
  } else {
    activeItems.value = activeItems.value.filter((i) => i.word !== word)
  }
}

function togglePresetGroup(group: { category: string; words: string[] }, checked: boolean | string | number) {
  if (checked) {
    for (const w of group.words) {
      if (!activeWordSet.value.has(w)) {
        activeItems.value.push({ word: w, category: group.category, preset: true })
      }
    }
  } else {
    activeItems.value = activeItems.value.filter((i) => !group.words.includes(i.word))
  }
}

function groupChecked(group: { category: string; words: string[] }) {
  return group.words.every((w) => activeWordSet.value.has(w))
}

function addManualWord() {
  const w = newWord.value.trim()
  if (!w) return ElMessage.warning('请输入违规词')
  if (activeWordSet.value.has(w)) return ElMessage.warning(`「${w}」已在标准中`)
  activeItems.value.push({ word: w, category: newWordCategory.value, preset: false })
  newWord.value = ''
}

function removeWordItem(word: string) {
  activeItems.value = activeItems.value.filter((i) => i.word !== word)
}

async function doScan() {
  scanning.value = true
  try {
    scanResult.value = await adminApi.violationScan()
    await loadPending()  // 扫描后刷新当前列表的违规标记
  } finally {
    scanning.value = false
  }
}

async function openWordsDialog() {
  const data = await adminApi.violationWords()
  const byCat: Record<string, string[]> = {}
  for (const p of data.presets || []) {
    const c = p.category || '通用'
    ;(byCat[c] = byCat[c] || []).push(p.word)
  }
  presetGroups.value = Object.entries(byCat).map(([category, words]) => ({ category, words }))
  vwCategories.value = data.categories || Object.keys(byCat)
  activeItems.value = (data.items || []).map((i: any) => ({
    word: i.word, category: i.category || '通用',
    preset: (data.presets || []).some((p: any) => p.word === i.word),
  }))
  wordsVisible.value = true
}

async function saveWords() {
  if (!activeItems.value.length) return ElMessage.warning('违规标准不能为空，至少保留一个词')
  savingWords.value = true
  try {
    const items = activeItems.value.map((i) => ({ word: i.word, category: i.category }))
    await adminApi.updateViolationWords(items)
    ElMessage.success(`违规标准已更新（${items.length} 个词）`)
    wordsVisible.value = false
    await loadPending(1)  // 按新标准重新识别当前待审列表
  } finally {
    savingWords.value = false
  }
}

function resetPending() {
  loadPending(1)
}

async function audit(p: any, action: 'approve' | 'reject') {
  await adminApi.audit(auditType.value, p.id, { action, reason: action === 'approve' ? '符合规范' : '内容不符合规范' })
  ElMessage.success(action === 'approve' ? '已通过' : '已拒绝')
  // 当前页删空后回退一页
  if (pendingItems.value.length <= 1 && pendingPage.value > 1) pendingPage.value -= 1
  await loadPending()
  await loadDash()
}

async function loadUsers(p = userPage.value) {
  userPage.value = p
  const data = await adminApi.users({
    keyword: userKw.value || undefined, role: userRole.value || undefined,
    page: p, page_size: 10,
  })
  users.value = data.items || []
  userTotal.value = data.total ?? users.value.length
}

function resetUsers() {
  loadUsers(1)
}

async function changeRole(row: any, role: string) {
  await adminApi.updateRole(row.id, role)
  ElMessage.success(`已将 ${row.nickname} 角色调整为 ${roleName(role)}`)
  await loadUsers()
}

async function toggleStatus(row: any) {
  const next = row.status === 'normal' ? 'banned' : 'normal'
  await adminApi.updateStatus(row.id, next)
  ElMessage.success(next === 'banned' ? '已封禁' : '已解封')
  await loadUsers()
}

async function loadCollectLogs(p = collectPage.value) {
  collectPage.value = p
  const data = await adminApi.collectLogs({ page: p, page_size: 10 })
  collectLogs.value = data.items || []
  collectTotal.value = data.total ?? collectLogs.value.length
}

async function loadData() {
  const s = await adminApi.dataSources()
  sources.value = s.items || s || []
  await loadCollectLogs(1)
}

async function doImport() {
  if (!importForm.csv_content.trim()) return ElMessage.warning('请填写 CSV 内容')
  importing.value = true
  try {
    await adminApi.importData({ ...importForm, csv_content: importForm.csv_content.trim() })
    ElMessage.success('导入完成，已写入采集日志')
    importForm.csv_content = ''
    await loadCollectLogs(1)
  } finally {
    importing.value = false
  }
}

async function loadLogs(p = logPage.value) {
  logPage.value = p
  const data = await adminApi.auditLogs({ page: p, page_size: 10 })
  auditLogs.value = data.items || []
  logTotal.value = data.total ?? auditLogs.value.length
}

/* ===== AI 知识库管理 ===== */
const kbDocs = ref<any[]>([])
const kbTotal = ref(0)
const kbPage = ref(1)
const kbKind = ref('')
const kbKeyword = ref('')
const kbStats = ref<any>(null)
const kbSync = ref<any>(null)
const kbResyncing = ref(false)
const kbAddVisible = ref(false)
const kbAdding = ref(false)
const kbAddForm = reactive({ title: '', url: '', content: '' })
const kbImportVisible = ref(false)
const kbDocImporting = ref(false)
const kbImportForm = reactive({ title: '' })
const kbImportFile = ref<File | null>(null)
const kbDragOver = ref(false)
const kbFileInput = ref<HTMLInputElement | null>(null)
const KB_ACCEPT = ['txt', 'md', 'markdown', 'csv', 'json', 'text', 'docx', 'pdf', 'xlsx', 'xls', 'html', 'htm']
const KB_MAX_MB = 20

const syncStateText = computed(() => {
  const s = kbSync.value || {}
  const map: Record<string, string> = {
    syncing: '同步中…', done: '已完成', partial: '部分完成',
    pending: '等待中', waiting_model: '等待模型', error: '异常',
  }
  return map[s.state] || s.state || '--'
})

function kindName(k: string) {
  return ({ people_article: '人民网资讯', baostock_quote: 'baostock 行情', manual: '手动录入' } as any)[k] || k
}

function kbTagType(kind: string) {
  return ({ people_article: 'danger', baostock_quote: 'primary', manual: 'success' } as any)[kind] || 'info'
}

async function loadKb(p = kbPage.value) {
  kbPage.value = p
  const data = await adminApi.kbDocuments({
    kind: kbKind.value || undefined, keyword: kbKeyword.value || undefined,
    page: p, page_size: 10,
  })
  kbDocs.value = data.items || []
  kbTotal.value = data.total ?? kbDocs.value.length
  kbStats.value = data.stats || null
  kbSync.value = data.sync || null
}

async function doKbAdd() {
  if (!kbAddForm.title.trim()) return ElMessage.warning('请填写标题')
  if (kbAddForm.content.trim().length < 10) return ElMessage.warning('正文内容至少 10 个字')
  kbAdding.value = true
  try {
    await adminApi.kbAddDocument({
      title: kbAddForm.title.trim(), content: kbAddForm.content.trim(),
      url: kbAddForm.url.trim() || undefined,
    })
    ElMessage.success('知识文档已入库')
    kbAddVisible.value = false
    kbAddForm.title = ''; kbAddForm.url = ''; kbAddForm.content = ''
    await loadKb(1)
  } finally {
    kbAdding.value = false
  }
}

function onKbFileChange(e: Event) {
  const target = e.target as HTMLInputElement
  const f = target.files && target.files.length ? target.files[0] : null
  if (f) setKbFile(f)
  // 允许重复选择同一文件
  target.value = ''
}

function triggerKbFileInput() {
  kbFileInput.value?.click()
}

function onKbDragOver() {
  kbDragOver.value = true
}

function onKbDragLeave() {
  kbDragOver.value = false
}

function onKbDrop(e: DragEvent) {
  kbDragOver.value = false
  const f = e.dataTransfer?.files && e.dataTransfer.files.length
    ? e.dataTransfer.files[0]
    : null
  if (f) setKbFile(f)
}

function setKbFile(f: File) {
  const ext = (f.name.split('.').pop() || '').toLowerCase()
  if (!KB_ACCEPT.includes(ext)) {
    ElMessage.warning(`不支持的格式：.${ext}，支持 ${KB_ACCEPT.join(' / ')}`)
    return
  }
  if (f.size > KB_MAX_MB * 1024 * 1024) {
    ElMessage.warning(`文件不能超过 ${KB_MAX_MB}MB（当前 ${(f.size / 1024 / 1024).toFixed(1)}MB）`)
    return
  }
  kbImportFile.value = f
}

function clearKbImportFile() {
  kbImportFile.value = null
}

async function doKbImport() {
  if (!kbImportFile.value) return ElMessage.warning('请先选择文档')
  kbDocImporting.value = true
  try {
    // http 拦截器成功时直接返回 ApiResponse.data（即导入结果对象）
    const d = await adminApi.kbImportDocument(
      kbImportFile.value, kbImportForm.title.trim() || undefined) || {}
    ElMessage.success(
      `已导入 ${d.imported ?? 0} 条知识（切分 ${d.chunks ?? 0} 段）` +
      (d.title ? `，标题：「${d.title}」` : ''))
    kbImportVisible.value = false
    kbImportForm.title = ''
    kbImportFile.value = null
    await loadKb(1)
  } catch (err: any) {
    const msg = err?.response?.data?.message || err?.message || '导入失败'
    ElMessage.error(msg)
  } finally {
    kbDocImporting.value = false
  }
}

async function delKbDoc(row: any) {
  await adminApi.kbDeleteDocument(row.id)
  ElMessage.success('已删除')
  if (kbDocs.value.length <= 1 && kbPage.value > 1) kbPage.value -= 1
  await loadKb()
}

async function doKbResync() {
  kbResyncing.value = true
  try {
    await adminApi.kbResync()
    ElMessage.success('已开始后台同步，稍后刷新查看结果')
    setTimeout(() => loadKb(), 4000)
  } finally {
    kbResyncing.value = false
  }
}

/* ===== 模型管理：百炼问答 / 识图开关 ===== */
const modelCfg = ref<any>(null)
const bailianToggling = ref(false)

async function loadModels() {
  const data = await adminApi.modelConfig()
  modelCfg.value = data
}

const TOGGLE_TIPS: Record<string, [string, string]> = {
  bailian_enabled: [
    '百炼大模型已开启：高级会员及以上 AI 问答将使用百炼 qwen-plus（失败自动降级本地）',
    '百炼大模型已关闭：所有用户恢复本地 qwen2.5:1.5b',
  ],
  bailian_vision_enabled: [
    '百炼识图模型已开启：高级会员及以上 AI 识图将使用百炼 qwen-vl-ocr（失败自动降级本地）',
    '百炼识图模型已关闭：所有用户恢复本地 minicpm-v4.6:latest',
  ],
}

async function toggleBailianField(field: 'bailian_enabled' | 'bailian_vision_enabled', val: boolean) {
  bailianToggling.value = true
  try {
    const data = await adminApi.updateModelConfig({ [field]: val })
    modelCfg.value = data
    const tips = TOGGLE_TIPS[field]
    ElMessage.success(val ? tips[0] : tips[1])
  } catch {
    if (modelCfg.value) modelCfg.value[field] = !val
  } finally {
    bailianToggling.value = false
  }
}

function onTab(name: string | number) {
  const loaders: Record<string, () => any> = {
    dashboard: loadDash, audit: loadPending, users: loadUsers, data: loadData, logs: loadLogs, kb: loadKb,
    models: loadModels,
  }
  loaders[String(name)]?.()
}

function resize() {
  riskChart?.resize()
  roleChart?.resize()
}

onMounted(() => {
  loadDash()
  window.addEventListener('resize', resize)
})
onBeforeUnmount(() => {
  window.removeEventListener('resize', resize)
  riskChart?.dispose()
  roleChart?.dispose()
})
</script>

<style scoped>
.wide { max-width: 1360px; }
/* ===== 模型管理 ===== */
.model-banner {
  display: flex; align-items: center; justify-content: space-between; gap: 16px; flex-wrap: wrap;
  background: var(--tyt-primary-soft); border: 1px solid rgba(99, 102, 241, .3);
  border-radius: 12px; padding: 14px 18px; margin-bottom: 16px;
}
.mb-title { font-size: 15px; font-weight: 700; margin-bottom: 4px; }
.mb-sub { font-size: 12px; font-weight: 500; margin-left: 8px; }
.mb-desc { font-size: 12.5px; line-height: 1.6; max-width: 860px; }
.mb-switch { display: flex; align-items: center; gap: 10px; flex-shrink: 0; }
.mb-state { font-size: 13px; font-weight: 600; color: var(--tyt-text-dim); }
.mb-state.on { color: #16a34a; }
.model-cards { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
@media (max-width: 900px) { .model-cards { grid-template-columns: 1fr; } }
.model-card {
  background: var(--tyt-card-2); border: 1px solid var(--tyt-border); border-radius: 12px; padding: 18px;
}
.model-card.mc-bailian { border-color: rgba(245, 158, 11, .45); }
.mc-head { display: flex; align-items: center; gap: 8px; margin-bottom: 10px; }
.mc-title { font-size: 15px; font-weight: 700; }
.mc-intro { font-size: 13px; line-height: 1.7; color: var(--tyt-text); margin: 0 0 10px; }
.mc-list { list-style: none; margin: 0 0 12px; padding: 0; }
.mc-list li { font-size: 12.5px; line-height: 1.9; color: var(--tyt-text); }
.mc-list li.mc-con { color: var(--tyt-text-dim); }
.mc-scope, .mc-meta { font-size: 12px; line-height: 1.8; border-top: 1px dashed var(--tyt-border); padding-top: 8px; }
.mc-meta { margin-top: 4px; }
.stat-cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 14px; margin-bottom: 18px; }
.stat { background: var(--tyt-card-2); border: 1px solid var(--tyt-border); border-radius: 12px;
  padding: 16px; text-align: center; }
.stat.warn { border-color: rgba(251, 191, 36, .4); }
.s-num { font-size: 26px; font-weight: 800; color: var(--tyt-primary); }
.stat.warn .s-num { color: var(--tyt-amber); }
.s-label { color: var(--tyt-text-dim); font-size: 12px; margin-top: 4px; }
.charts { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.chart-box { height: 280px; background: var(--tyt-card-2); border-radius: 12px; border: 1px solid var(--tyt-border); }
.audit-tabs { margin-bottom: 14px; display: flex; align-items: center; justify-content: space-between; gap: 12px; flex-wrap: wrap; }
.audit-ops { display: flex; gap: 8px; }
.scan-result {
  display: flex; align-items: center; gap: 12px; flex-wrap: wrap;
  background: var(--tyt-primary-soft); border: 1px solid rgba(99, 102, 241, .3);
  border-radius: 10px; padding: 10px 14px; margin-bottom: 12px; font-size: 13px;
}
.scan-summary b { color: #dc2626; }
.scan-close {
  margin-left: auto; border: none; background: none; cursor: pointer;
  color: var(--tyt-text-dim); font-size: 12px;
}
.scan-close:hover { color: var(--tyt-primary-dark); }
.p-violation { border-color: rgba(220, 38, 38, .45); }
.p-violation-warn {
  margin: 0 0 8px; padding: 6px 10px; border-radius: 8px; font-size: 12.5px;
  background: rgba(220, 38, 38, .08); border: 1px solid rgba(220, 38, 38, .25);
  color: #dc2626; font-weight: 600;
}
.words-tip { margin: 0 0 10px; font-size: 12.5px; line-height: 1.7; }
/* 违规标准对话框：预设勾选 + 手动添加 + 当前标准（参考第一版布局） */
.vw-section { margin-bottom: 14px; }
.vw-section-title { font-size: 13px; font-weight: 600; margin-bottom: 8px; }
.vw-groups { max-height: 210px; overflow-y: auto; border: 1px solid var(--tyt-border);
  border-radius: 8px; padding: 10px 12px; }
.vw-group { padding: 4px 0 8px; border-bottom: 1px dashed var(--tyt-border); }
.vw-group:last-child { border-bottom: none; }
.vw-group-check { font-weight: 600; margin-right: 10px; }
.vw-group-words { display: flex; flex-wrap: wrap; gap: 2px 14px; padding-left: 24px; }
.vw-add-row { display: flex; gap: 8px; }
.vw-active { display: flex; flex-wrap: wrap; gap: 6px; min-height: 40px; max-height: 150px;
  overflow-y: auto; border: 1px solid var(--tyt-border); border-radius: 8px; padding: 10px; }
.vw-chip { display: inline-flex; align-items: center; gap: 4px; padding: 3px 10px;
  border-radius: 14px; font-size: 12.5px; border: 1px solid rgba(99,102,241,.3);
  background: var(--tyt-primary-soft, rgba(99,102,241,.08)); color: var(--tyt-primary-dark, #4338ca); }
.vw-chip em { font-style: normal; font-size: 10.5px; opacity: .75; }
.vw-chip-custom { border-color: rgba(245,158,11,.45); background: rgba(245,158,11,.1); color: #b45309; }
.vw-chip-del { cursor: pointer; font-style: normal; margin-left: 4px; font-size: 13px;
  line-height: 1; opacity: .65; }
.vw-chip-del:hover { opacity: 1; color: #ef4444; }
.p-item { border: 1px solid var(--tyt-border); border-radius: 10px; padding: 12px 14px; margin-bottom: 10px; }
.pager { display: flex; justify-content: center; margin-top: 14px; }
.p-head { display: flex; align-items: center; gap: 10px; margin-bottom: 6px; flex-wrap: wrap; }
.p-title { font-weight: 600; font-size: 13.5px; }
.p-date { margin-left: auto; font-size: 12px; }
.p-content { margin: 0 0 8px; color: var(--tyt-text-dim); font-size: 13px; line-height: 1.8; }
.p-imgs { display: flex; flex-wrap: wrap; gap: 6px; margin: 0 0 8px; }
.p-img { width: 64px; height: 64px; border-radius: 6px; overflow: hidden; cursor: zoom-in;
  border: 1px solid var(--tyt-border); }
.p-actions { display: flex; gap: 8px; }
.user-filter { display: flex; gap: 10px; margin-bottom: 12px; }
h4 { margin: 18px 0 10px; font-size: 14px; }
.import-form { display: flex; gap: 10px; margin-bottom: 10px; }
.csv-input { margin-bottom: 6px; }
.kb-head { display: flex; align-items: center; justify-content: space-between; gap: 12px; flex-wrap: wrap; margin-bottom: 14px; }
.kb-stat-pills { display: flex; gap: 8px; flex-wrap: wrap; }
.kb-pill {
  font-size: 12px; border-radius: 999px; padding: 4px 12px;
  background: var(--tyt-card-2); border: 1px solid var(--tyt-border); color: var(--tyt-text-dim);
}
.kb-pill.total { background: var(--tyt-primary-soft); color: var(--tyt-primary-dark); font-weight: 600; }
.kb-pill.sync { color: var(--tyt-primary-dark); }
.kb-filter { display: flex; gap: 10px; margin-bottom: 12px; }
.kb-excerpt { font-size: 12px; color: var(--tyt-text-dim); word-break: break-all; }
.detail-json { font-size: 11px; color: var(--tyt-text-dim); word-break: break-all; }
/* 文档导入拖拽区 */
.kb-dropzone {
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  border: 1.5px dashed var(--tyt-border);
  border-radius: 12px;
  background: var(--tyt-card-2);
  padding: 26px 16px;
  text-align: center;
  cursor: pointer;
  transition: border-color .18s, background .18s, box-shadow .18s;
  user-select: none;
}
.kb-dropzone.is-dragover {
  border-color: var(--tyt-primary, #6366f1);
  background: rgba(99, 102, 241, .08);
  box-shadow: 0 0 0 3px rgba(99, 102, 241, .15);
}
.kb-dropzone.has-file { cursor: default; border-style: solid; }
.kb-dropzone .dz-icon { font-size: 30px; line-height: 1; margin-bottom: 8px; }
.kb-dropzone .dz-main { font-size: 14px; font-weight: 600; color: var(--tyt-text); }
.kb-dropzone .dz-link { color: var(--tyt-primary, #6366f1); text-decoration: underline; margin-left: 2px; }
.kb-dropzone .dz-sub { font-size: 12px; margin-top: 4px; }
.kb-dropzone .dz-file {
  display: inline-flex; align-items: center; gap: 8px;
  font-size: 14px; font-weight: 600; color: var(--tyt-text);
  max-width: 100%; flex-wrap: wrap; justify-content: center;
}
.kb-dropzone .dz-file-name {
  max-width: 280px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.kb-dropzone .dz-file-icon { font-size: 18px; }
.kb-file-input { display: none; }
:deep(.el-tabs__content) { padding-bottom: 10px; }
</style>
