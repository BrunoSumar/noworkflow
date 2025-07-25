import {
  select as d3_select,
  Selection as d3_Selection,
  BaseType as d3_BaseType,
} from 'd3-selection';

import {Widget} from '@lumino/widgets';

import {TrialGraph, TrialGraphData, ActivationData} from '@noworkflow/trial';

import {json} from '@noworkflow/utils';

export
class BaseActivationGraphWidget extends Widget {

  name: string;
  cls: string;
  t1: string;
  t2: string;
  graph: TrialGraph;
  d3node: d3_Selection<d3_BaseType, {}, HTMLElement | null, any>;

  static graphTypeForm(name: string, selectorDiv: d3_Selection<d3_BaseType, {}, HTMLElement | null, any>) {
    let graphType = selectorDiv.append("div")
      .classed("graph-attr", true);

    graphType.append("label")
      .attr("for", name + "-graphtype")
      .attr("title", "Select the graph type")
      .text("Graph Type:")

    let typeOptions = graphType.append("select")
      .attr("id", name + "-graphtype")
      .classed("graph-type", true)
      .classed("select-style", true);

    typeOptions.append("option")
      .attr("value", "tree")
      .attr("data-description", "Activation tree. Edges represent order of execution")
      .text("Activation Tree")

    typeOptions.append("option")
      .attr("value", "no_match")
      .attr("data-description", "Activation tree presented as a Graph")
      .text("Activation No Match")

    typeOptions.append("option")
      .attr("value", "exact_match")
      .attr("data-description", "Calls have counting independent from caller activations")
      .text("Activation Exact Match")

    typeOptions.append("option")
      .attr("value", "namespace_match")
      .attr("data-description", "Calls are combined and a function may have more than one call workflow")
      .text("Activation Namespace Match")

    typeOptions.append("option")
    .attr("value", "definition_tree")
    .attr("data-description", "Definition tree. Edges represent order of script definition")
    .text("Definition Tree")

    typeOptions.property("value", "namespace_match")
  }

  static useCacheForm(name: string, selectorDiv: d3_Selection<d3_BaseType, {}, HTMLElement | null, any>) {
    let useCache = selectorDiv.append("div")
      .classed("graph-attr", true);

    useCache.append("input")
      .attr("type", "checkbox")
      .attr("name", "use_cache")
      .attr("value", "on")
      .attr("checked", true)
      .classed("use-cache", true)
      .attr("id", name + "-use-cache")

    useCache.append("label")
      .attr("for", name + "-use-cache")
      .attr("title", "Select the graph type")
      .text("Use Cache")
  }

  static createNode(name:string, fn: (name: string, parent: d3_Selection<d3_BaseType, {}, HTMLElement | null, any>) => void = (parent) => null): HTMLElement {
    let node = document.createElement('div');
    let d3node = d3_select<HTMLDivElement, any>(node);

    let content = d3node.append('div')
      .classed('trial-content', true)

    let selectorDiv = content.append("div")
      .classed("graphselector", true)
      .classed("hide-toolbar", true);

    BaseActivationGraphWidget.graphTypeForm(name, selectorDiv);

    fn(name, selectorDiv);

    BaseActivationGraphWidget.useCacheForm(name, selectorDiv);

    let selectorReload = selectorDiv.append("a")
      .attr("href", "#")
      .classed("link-button reload-button", true)

    selectorReload.append('i')
      .classed("fa fa-refresh", true);

    selectorReload.append('span')
      .text('Reload');

    content.append('div')
      .classed('sub-content', true);

    return node;
  }

  setGraph(data: TrialGraphData, config: any={}, showDiffFunction?:any, nowVisPanel?: any) {
    let sub = this.node.getElementsByClassName("sub-content")[0];
    sub.innerHTML = "";
    this.graph = new TrialGraph(this.cls, sub, config, showDiffFunction, nowVisPanel);
    this.graph.load(data, this.t1, this.t2);
  }

  graphDefinition(selectedGraph: string = "namespace_match", useCache: boolean = true, genDataflow: boolean = true, data: TrialGraphData) {
    return {
      width: this.node.getBoundingClientRect().width - 24,
      height: this.node.getBoundingClientRect().height - 24,
      customForm: (graph: TrialGraph, form: d3_Selection<d3_BaseType, {}, HTMLElement | null, any>) => {
        // Toggle Tooltips
        let selectorDiv = this.d3node.select(".trial-content .graphselector");

        let typeOptions = selectorDiv.select(".graph-type");
        typeOptions.property("value", selectedGraph);

        let useCacheDiv = selectorDiv.select(".use-cache");
        useCacheDiv.property("checked", useCache);


        let selectorToggle = form.append("input")
          .attr("id", "trial-" + graph.graphId + "-toolbar-selector-check")
          .attr("type", "checkbox")
          .attr("name", "trial-toolbar-selector-check")
          .attr("value", "show")
          .property("checked", selectorDiv.classed('visible'))
          .on("change", () => {
            let visible = selectorToggle.property("checked");
            selectorToggleI
              .classed('fa-circle-o', visible)
              .classed('fa-circle', !visible);
            selectorDiv
              .classed('visible', visible)
              .classed('show-toolbar', visible)
              .classed('hide-toolbar', !visible)
          });
        let selectorLabel = form.append("label")
          .attr("for", "trial-" + graph.graphId + "-toolbar-selector-check")

        let optionsNode: any = typeOptions.node();

        selectorLabel.append("span")
          .classed("toggle-label", true)
          .text(optionsNode.options[optionsNode.selectedIndex].text)

        let selectorToggleI = selectorLabel.append("i")
          .classed('fa', true)
          .classed("fa-circle", !selectorDiv.classed('visible'))
          .classed("fa-circle-o", selectorDiv.classed('visible'))
      },
      customLoadTooltip: (g: TrialGraph, div: HTMLDivElement, text: string, trialid: string, aid: string) => {
        var url = "/trials/" + trialid + "/activations/" + aid + ".json";
        function createResponse(activationId: string, div2: Element) {
          return function(data: ActivationData) {
            g.activationStorage[activationId] = data;
            g.updateTooltipDiv(activationId, div2);
          }
        }
        json(text, div, url, createResponse(aid, div));
      },
      genDataflow: genDataflow,
      queryTooltip: true
    }
  }

  configureGraph(selectedGraph: string = "namespace_match", useCache: boolean = true, genDataflow: boolean = true, data: TrialGraphData, showDiffFunction?:any, nowVisPanel?:any) {
    this.setGraph(data, this.graphDefinition(selectedGraph, useCache, genDataflow, data), showDiffFunction, nowVisPanel);
  }

  protected onResize(msg: Widget.ResizeMessage): void {
    if (this.graph) {
      this.graph.config.width = this.node.getBoundingClientRect().width - 24;
      this.graph.config.height = this.node.getBoundingClientRect().height - 24;
      this.graph.updateWindow();
    }
  }

}
