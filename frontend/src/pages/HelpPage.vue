<script setup lang="ts">
import Icon from '../components/Icon.vue'
</script>
<template>
  <div class="page-heading">
    <div>
      <div class="page-kicker">GETTING STARTED</div>
      <h1>使用指南</h1>
      <p>把一个采集脚本，变成按时运行的数据工作。</p>
    </div>
    <span class="badge">FlowHarbor v0.1.0</span>
  </div>
  <div class="help-grid">
    <section class="panel">
      <div class="panel-header">
        <h3 class="line">
          <Icon name="spiders" :size="18" />
          创建第一个任务
        </h3>
      </div>
      <div class="panel-body">
        <ol>
          <li>在「项目与任务」中新建项目，用来组织采集任务。</li>
          <li>新建任务，选择项目，填写名称与运行命令。</li>
          <li>点击「代码」，上传 UTF-8 编码的 Python 脚本。</li>
          <li>点击「运行」，选择节点并确认命令参数。</li>
          <li>前往「执行记录」查看状态、日志与结果。</li>
        </ol>
        <p>
          示例脚本及依赖配置位于源码交付包的
          <code>examples/</code>
          目录。先安装任务依赖，再运行脚本。
        </p>
      </div>
    </section>
    <section class="panel">
      <div class="panel-header">
        <h3 class="line">
          <Icon name="schedules" :size="18" />
          安排定时执行
        </h3>
      </div>
      <div class="panel-body">
        <p>进入「定时计划」，选择任务，填写五位 Cron 表达式。时间以部署时的服务时区为准。</p>
        <pre>
*/5 * * * *   每 5 分钟
0 9 * * *     每天 09:00
0 9 * * 1-5   周一至周五 09:00</pre
        >
        <p>确认计划的运行命令与参数后启用计划。暂时不需要运行时，可以停用并保留配置。</p>
      </div>
    </section>
    <section class="panel">
      <div class="panel-header">
        <h3 class="line">
          <Icon name="runs" :size="18" />
          查看结果与定位问题
        </h3>
      </div>
      <div class="panel-body">
        <p>
          执行详情中包含日志和结果两个页签。日志来自脚本标准输出；采集结果需要通过 Crawlab SDK
          保存，普通文件输出不会自动出现在结果页。
        </p>
        <p>
          失败时先检查日志中的异常，再核对 Worker
          是否安装了依赖、命令是否正确、采集目标是否可访问。修正后可以重新执行。
        </p>
        <p>结果页提供当前页 JSON 下载。完整数据导出和数据源管理可使用 Crawlab 原生管理功能。</p>
      </div>
    </section>
    <section class="panel">
      <div class="panel-header">
        <h3 class="line">
          <Icon name="nodes" :size="18" />
          部署与产品信息
        </h3>
      </div>
      <div class="panel-body">
        <p>
          FlowHarbor 提供独立调度工作台，通过 Crawlab API 管理任务。执行引擎采用 Master / Worker
          架构，适用于单团队私有化部署。
        </p>
        <p>
          使用源码包中的
          <code>README.md</code>
          与
          <code>docs/</code>
          完成启动、环境配置、备份恢复和版本发布。生产部署请按手册完成账户初始化与 HTTPS 配置。
        </p>
        <p>引擎：Crawlab 0.6.3 · 界面：Vue 3 · 接入服务：FastAPI</p>
        <a href="https://github.com/crawlab-team/crawlab" target="_blank" rel="noreferrer">
          Crawlab 官方项目 ↗
        </a>
      </div>
    </section>
  </div>
</template>
