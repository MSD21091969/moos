"use strict";
(() => {
  var __create = Object.create;
  var __defProp = Object.defineProperty;
  var __getOwnPropDesc = Object.getOwnPropertyDescriptor;
  var __getOwnPropNames = Object.getOwnPropertyNames;
  var __getProtoOf = Object.getPrototypeOf;
  var __hasOwnProp = Object.prototype.hasOwnProperty;
  var __commonJS = (cb, mod) => function __require() {
    return mod || (0, cb[__getOwnPropNames(cb)[0]])((mod = { exports: {} }).exports, mod), mod.exports;
  };
  var __copyProps = (to, from, except, desc) => {
    if (from && typeof from === "object" || typeof from === "function") {
      for (let key of __getOwnPropNames(from))
        if (!__hasOwnProp.call(to, key) && key !== except)
          __defProp(to, key, { get: () => from[key], enumerable: !(desc = __getOwnPropDesc(from, key)) || desc.enumerable });
    }
    return to;
  };
  var __toESM = (mod, isNodeMode, target) => (target = mod != null ? __create(__getProtoOf(mod)) : {}, __copyProps(
    // If the importer is in node compatibility mode or this is not an ESM
    // file that has been converted to a CommonJS file using a Babel-
    // compatible transform (i.e. "__esModule" has not been set), then set
    // "default" to the CommonJS "module.exports" for node compatibility.
    isNodeMode || !mod || !mod.__esModule ? __defProp(target, "default", { value: mod, enumerable: true }) : target,
    mod
  ));

  // node_modules/react/cjs/react.development.js
  var require_react_development = __commonJS({
    "node_modules/react/cjs/react.development.js"(exports, module) {
      "use strict";
      if (true) {
        (function() {
          "use strict";
          if (typeof __REACT_DEVTOOLS_GLOBAL_HOOK__ !== "undefined" && typeof __REACT_DEVTOOLS_GLOBAL_HOOK__.registerInternalModuleStart === "function") {
            __REACT_DEVTOOLS_GLOBAL_HOOK__.registerInternalModuleStart(new Error());
          }
          var ReactVersion = "18.3.1";
          var REACT_ELEMENT_TYPE = Symbol.for("react.element");
          var REACT_PORTAL_TYPE = Symbol.for("react.portal");
          var REACT_FRAGMENT_TYPE = Symbol.for("react.fragment");
          var REACT_STRICT_MODE_TYPE = Symbol.for("react.strict_mode");
          var REACT_PROFILER_TYPE = Symbol.for("react.profiler");
          var REACT_PROVIDER_TYPE = Symbol.for("react.provider");
          var REACT_CONTEXT_TYPE = Symbol.for("react.context");
          var REACT_FORWARD_REF_TYPE = Symbol.for("react.forward_ref");
          var REACT_SUSPENSE_TYPE = Symbol.for("react.suspense");
          var REACT_SUSPENSE_LIST_TYPE = Symbol.for("react.suspense_list");
          var REACT_MEMO_TYPE = Symbol.for("react.memo");
          var REACT_LAZY_TYPE = Symbol.for("react.lazy");
          var REACT_OFFSCREEN_TYPE = Symbol.for("react.offscreen");
          var MAYBE_ITERATOR_SYMBOL = Symbol.iterator;
          var FAUX_ITERATOR_SYMBOL = "@@iterator";
          function getIteratorFn(maybeIterable) {
            if (maybeIterable === null || typeof maybeIterable !== "object") {
              return null;
            }
            var maybeIterator = MAYBE_ITERATOR_SYMBOL && maybeIterable[MAYBE_ITERATOR_SYMBOL] || maybeIterable[FAUX_ITERATOR_SYMBOL];
            if (typeof maybeIterator === "function") {
              return maybeIterator;
            }
            return null;
          }
          var ReactCurrentDispatcher = {
            /**
             * @internal
             * @type {ReactComponent}
             */
            current: null
          };
          var ReactCurrentBatchConfig = {
            transition: null
          };
          var ReactCurrentActQueue = {
            current: null,
            // Used to reproduce behavior of `batchedUpdates` in legacy mode.
            isBatchingLegacy: false,
            didScheduleLegacyUpdate: false
          };
          var ReactCurrentOwner = {
            /**
             * @internal
             * @type {ReactComponent}
             */
            current: null
          };
          var ReactDebugCurrentFrame = {};
          var currentExtraStackFrame = null;
          function setExtraStackFrame(stack) {
            {
              currentExtraStackFrame = stack;
            }
          }
          {
            ReactDebugCurrentFrame.setExtraStackFrame = function(stack) {
              {
                currentExtraStackFrame = stack;
              }
            };
            ReactDebugCurrentFrame.getCurrentStack = null;
            ReactDebugCurrentFrame.getStackAddendum = function() {
              var stack = "";
              if (currentExtraStackFrame) {
                stack += currentExtraStackFrame;
              }
              var impl = ReactDebugCurrentFrame.getCurrentStack;
              if (impl) {
                stack += impl() || "";
              }
              return stack;
            };
          }
          var enableScopeAPI = false;
          var enableCacheElement = false;
          var enableTransitionTracing = false;
          var enableLegacyHidden = false;
          var enableDebugTracing = false;
          var ReactSharedInternals = {
            ReactCurrentDispatcher,
            ReactCurrentBatchConfig,
            ReactCurrentOwner
          };
          {
            ReactSharedInternals.ReactDebugCurrentFrame = ReactDebugCurrentFrame;
            ReactSharedInternals.ReactCurrentActQueue = ReactCurrentActQueue;
          }
          function warn(format) {
            {
              {
                for (var _len = arguments.length, args = new Array(_len > 1 ? _len - 1 : 0), _key = 1; _key < _len; _key++) {
                  args[_key - 1] = arguments[_key];
                }
                printWarning("warn", format, args);
              }
            }
          }
          function error(format) {
            {
              {
                for (var _len2 = arguments.length, args = new Array(_len2 > 1 ? _len2 - 1 : 0), _key2 = 1; _key2 < _len2; _key2++) {
                  args[_key2 - 1] = arguments[_key2];
                }
                printWarning("error", format, args);
              }
            }
          }
          function printWarning(level, format, args) {
            {
              var ReactDebugCurrentFrame2 = ReactSharedInternals.ReactDebugCurrentFrame;
              var stack = ReactDebugCurrentFrame2.getStackAddendum();
              if (stack !== "") {
                format += "%s";
                args = args.concat([stack]);
              }
              var argsWithFormat = args.map(function(item) {
                return String(item);
              });
              argsWithFormat.unshift("Warning: " + format);
              Function.prototype.apply.call(console[level], console, argsWithFormat);
            }
          }
          var didWarnStateUpdateForUnmountedComponent = {};
          function warnNoop(publicInstance, callerName) {
            {
              var _constructor = publicInstance.constructor;
              var componentName = _constructor && (_constructor.displayName || _constructor.name) || "ReactClass";
              var warningKey = componentName + "." + callerName;
              if (didWarnStateUpdateForUnmountedComponent[warningKey]) {
                return;
              }
              error("Can't call %s on a component that is not yet mounted. This is a no-op, but it might indicate a bug in your application. Instead, assign to `this.state` directly or define a `state = {};` class property with the desired state in the %s component.", callerName, componentName);
              didWarnStateUpdateForUnmountedComponent[warningKey] = true;
            }
          }
          var ReactNoopUpdateQueue = {
            /**
             * Checks whether or not this composite component is mounted.
             * @param {ReactClass} publicInstance The instance we want to test.
             * @return {boolean} True if mounted, false otherwise.
             * @protected
             * @final
             */
            isMounted: function(publicInstance) {
              return false;
            },
            /**
             * Forces an update. This should only be invoked when it is known with
             * certainty that we are **not** in a DOM transaction.
             *
             * You may want to call this when you know that some deeper aspect of the
             * component's state has changed but `setState` was not called.
             *
             * This will not invoke `shouldComponentUpdate`, but it will invoke
             * `componentWillUpdate` and `componentDidUpdate`.
             *
             * @param {ReactClass} publicInstance The instance that should rerender.
             * @param {?function} callback Called after component is updated.
             * @param {?string} callerName name of the calling function in the public API.
             * @internal
             */
            enqueueForceUpdate: function(publicInstance, callback, callerName) {
              warnNoop(publicInstance, "forceUpdate");
            },
            /**
             * Replaces all of the state. Always use this or `setState` to mutate state.
             * You should treat `this.state` as immutable.
             *
             * There is no guarantee that `this.state` will be immediately updated, so
             * accessing `this.state` after calling this method may return the old value.
             *
             * @param {ReactClass} publicInstance The instance that should rerender.
             * @param {object} completeState Next state.
             * @param {?function} callback Called after component is updated.
             * @param {?string} callerName name of the calling function in the public API.
             * @internal
             */
            enqueueReplaceState: function(publicInstance, completeState, callback, callerName) {
              warnNoop(publicInstance, "replaceState");
            },
            /**
             * Sets a subset of the state. This only exists because _pendingState is
             * internal. This provides a merging strategy that is not available to deep
             * properties which is confusing. TODO: Expose pendingState or don't use it
             * during the merge.
             *
             * @param {ReactClass} publicInstance The instance that should rerender.
             * @param {object} partialState Next partial state to be merged with state.
             * @param {?function} callback Called after component is updated.
             * @param {?string} Name of the calling function in the public API.
             * @internal
             */
            enqueueSetState: function(publicInstance, partialState, callback, callerName) {
              warnNoop(publicInstance, "setState");
            }
          };
          var assign = Object.assign;
          var emptyObject = {};
          {
            Object.freeze(emptyObject);
          }
          function Component(props, context, updater) {
            this.props = props;
            this.context = context;
            this.refs = emptyObject;
            this.updater = updater || ReactNoopUpdateQueue;
          }
          Component.prototype.isReactComponent = {};
          Component.prototype.setState = function(partialState, callback) {
            if (typeof partialState !== "object" && typeof partialState !== "function" && partialState != null) {
              throw new Error("setState(...): takes an object of state variables to update or a function which returns an object of state variables.");
            }
            this.updater.enqueueSetState(this, partialState, callback, "setState");
          };
          Component.prototype.forceUpdate = function(callback) {
            this.updater.enqueueForceUpdate(this, callback, "forceUpdate");
          };
          {
            var deprecatedAPIs = {
              isMounted: ["isMounted", "Instead, make sure to clean up subscriptions and pending requests in componentWillUnmount to prevent memory leaks."],
              replaceState: ["replaceState", "Refactor your code to use setState instead (see https://github.com/facebook/react/issues/3236)."]
            };
            var defineDeprecationWarning = function(methodName, info) {
              Object.defineProperty(Component.prototype, methodName, {
                get: function() {
                  warn("%s(...) is deprecated in plain JavaScript React classes. %s", info[0], info[1]);
                  return void 0;
                }
              });
            };
            for (var fnName in deprecatedAPIs) {
              if (deprecatedAPIs.hasOwnProperty(fnName)) {
                defineDeprecationWarning(fnName, deprecatedAPIs[fnName]);
              }
            }
          }
          function ComponentDummy() {
          }
          ComponentDummy.prototype = Component.prototype;
          function PureComponent(props, context, updater) {
            this.props = props;
            this.context = context;
            this.refs = emptyObject;
            this.updater = updater || ReactNoopUpdateQueue;
          }
          var pureComponentPrototype = PureComponent.prototype = new ComponentDummy();
          pureComponentPrototype.constructor = PureComponent;
          assign(pureComponentPrototype, Component.prototype);
          pureComponentPrototype.isPureReactComponent = true;
          function createRef() {
            var refObject = {
              current: null
            };
            {
              Object.seal(refObject);
            }
            return refObject;
          }
          var isArrayImpl = Array.isArray;
          function isArray(a) {
            return isArrayImpl(a);
          }
          function typeName(value) {
            {
              var hasToStringTag = typeof Symbol === "function" && Symbol.toStringTag;
              var type = hasToStringTag && value[Symbol.toStringTag] || value.constructor.name || "Object";
              return type;
            }
          }
          function willCoercionThrow(value) {
            {
              try {
                testStringCoercion(value);
                return false;
              } catch (e) {
                return true;
              }
            }
          }
          function testStringCoercion(value) {
            return "" + value;
          }
          function checkKeyStringCoercion(value) {
            {
              if (willCoercionThrow(value)) {
                error("The provided key is an unsupported type %s. This value must be coerced to a string before before using it here.", typeName(value));
                return testStringCoercion(value);
              }
            }
          }
          function getWrappedName(outerType, innerType, wrapperName) {
            var displayName = outerType.displayName;
            if (displayName) {
              return displayName;
            }
            var functionName = innerType.displayName || innerType.name || "";
            return functionName !== "" ? wrapperName + "(" + functionName + ")" : wrapperName;
          }
          function getContextName(type) {
            return type.displayName || "Context";
          }
          function getComponentNameFromType(type) {
            if (type == null) {
              return null;
            }
            {
              if (typeof type.tag === "number") {
                error("Received an unexpected object in getComponentNameFromType(). This is likely a bug in React. Please file an issue.");
              }
            }
            if (typeof type === "function") {
              return type.displayName || type.name || null;
            }
            if (typeof type === "string") {
              return type;
            }
            switch (type) {
              case REACT_FRAGMENT_TYPE:
                return "Fragment";
              case REACT_PORTAL_TYPE:
                return "Portal";
              case REACT_PROFILER_TYPE:
                return "Profiler";
              case REACT_STRICT_MODE_TYPE:
                return "StrictMode";
              case REACT_SUSPENSE_TYPE:
                return "Suspense";
              case REACT_SUSPENSE_LIST_TYPE:
                return "SuspenseList";
            }
            if (typeof type === "object") {
              switch (type.$$typeof) {
                case REACT_CONTEXT_TYPE:
                  var context = type;
                  return getContextName(context) + ".Consumer";
                case REACT_PROVIDER_TYPE:
                  var provider = type;
                  return getContextName(provider._context) + ".Provider";
                case REACT_FORWARD_REF_TYPE:
                  return getWrappedName(type, type.render, "ForwardRef");
                case REACT_MEMO_TYPE:
                  var outerName = type.displayName || null;
                  if (outerName !== null) {
                    return outerName;
                  }
                  return getComponentNameFromType(type.type) || "Memo";
                case REACT_LAZY_TYPE: {
                  var lazyComponent = type;
                  var payload = lazyComponent._payload;
                  var init = lazyComponent._init;
                  try {
                    return getComponentNameFromType(init(payload));
                  } catch (x) {
                    return null;
                  }
                }
              }
            }
            return null;
          }
          var hasOwnProperty = Object.prototype.hasOwnProperty;
          var RESERVED_PROPS = {
            key: true,
            ref: true,
            __self: true,
            __source: true
          };
          var specialPropKeyWarningShown, specialPropRefWarningShown, didWarnAboutStringRefs;
          {
            didWarnAboutStringRefs = {};
          }
          function hasValidRef(config) {
            {
              if (hasOwnProperty.call(config, "ref")) {
                var getter = Object.getOwnPropertyDescriptor(config, "ref").get;
                if (getter && getter.isReactWarning) {
                  return false;
                }
              }
            }
            return config.ref !== void 0;
          }
          function hasValidKey(config) {
            {
              if (hasOwnProperty.call(config, "key")) {
                var getter = Object.getOwnPropertyDescriptor(config, "key").get;
                if (getter && getter.isReactWarning) {
                  return false;
                }
              }
            }
            return config.key !== void 0;
          }
          function defineKeyPropWarningGetter(props, displayName) {
            var warnAboutAccessingKey = function() {
              {
                if (!specialPropKeyWarningShown) {
                  specialPropKeyWarningShown = true;
                  error("%s: `key` is not a prop. Trying to access it will result in `undefined` being returned. If you need to access the same value within the child component, you should pass it as a different prop. (https://reactjs.org/link/special-props)", displayName);
                }
              }
            };
            warnAboutAccessingKey.isReactWarning = true;
            Object.defineProperty(props, "key", {
              get: warnAboutAccessingKey,
              configurable: true
            });
          }
          function defineRefPropWarningGetter(props, displayName) {
            var warnAboutAccessingRef = function() {
              {
                if (!specialPropRefWarningShown) {
                  specialPropRefWarningShown = true;
                  error("%s: `ref` is not a prop. Trying to access it will result in `undefined` being returned. If you need to access the same value within the child component, you should pass it as a different prop. (https://reactjs.org/link/special-props)", displayName);
                }
              }
            };
            warnAboutAccessingRef.isReactWarning = true;
            Object.defineProperty(props, "ref", {
              get: warnAboutAccessingRef,
              configurable: true
            });
          }
          function warnIfStringRefCannotBeAutoConverted(config) {
            {
              if (typeof config.ref === "string" && ReactCurrentOwner.current && config.__self && ReactCurrentOwner.current.stateNode !== config.__self) {
                var componentName = getComponentNameFromType(ReactCurrentOwner.current.type);
                if (!didWarnAboutStringRefs[componentName]) {
                  error('Component "%s" contains the string ref "%s". Support for string refs will be removed in a future major release. This case cannot be automatically converted to an arrow function. We ask you to manually fix this case by using useRef() or createRef() instead. Learn more about using refs safely here: https://reactjs.org/link/strict-mode-string-ref', componentName, config.ref);
                  didWarnAboutStringRefs[componentName] = true;
                }
              }
            }
          }
          var ReactElement = function(type, key, ref, self, source, owner, props) {
            var element = {
              // This tag allows us to uniquely identify this as a React Element
              $$typeof: REACT_ELEMENT_TYPE,
              // Built-in properties that belong on the element
              type,
              key,
              ref,
              props,
              // Record the component responsible for creating this element.
              _owner: owner
            };
            {
              element._store = {};
              Object.defineProperty(element._store, "validated", {
                configurable: false,
                enumerable: false,
                writable: true,
                value: false
              });
              Object.defineProperty(element, "_self", {
                configurable: false,
                enumerable: false,
                writable: false,
                value: self
              });
              Object.defineProperty(element, "_source", {
                configurable: false,
                enumerable: false,
                writable: false,
                value: source
              });
              if (Object.freeze) {
                Object.freeze(element.props);
                Object.freeze(element);
              }
            }
            return element;
          };
          function createElement(type, config, children) {
            var propName;
            var props = {};
            var key = null;
            var ref = null;
            var self = null;
            var source = null;
            if (config != null) {
              if (hasValidRef(config)) {
                ref = config.ref;
                {
                  warnIfStringRefCannotBeAutoConverted(config);
                }
              }
              if (hasValidKey(config)) {
                {
                  checkKeyStringCoercion(config.key);
                }
                key = "" + config.key;
              }
              self = config.__self === void 0 ? null : config.__self;
              source = config.__source === void 0 ? null : config.__source;
              for (propName in config) {
                if (hasOwnProperty.call(config, propName) && !RESERVED_PROPS.hasOwnProperty(propName)) {
                  props[propName] = config[propName];
                }
              }
            }
            var childrenLength = arguments.length - 2;
            if (childrenLength === 1) {
              props.children = children;
            } else if (childrenLength > 1) {
              var childArray = Array(childrenLength);
              for (var i = 0; i < childrenLength; i++) {
                childArray[i] = arguments[i + 2];
              }
              {
                if (Object.freeze) {
                  Object.freeze(childArray);
                }
              }
              props.children = childArray;
            }
            if (type && type.defaultProps) {
              var defaultProps = type.defaultProps;
              for (propName in defaultProps) {
                if (props[propName] === void 0) {
                  props[propName] = defaultProps[propName];
                }
              }
            }
            {
              if (key || ref) {
                var displayName = typeof type === "function" ? type.displayName || type.name || "Unknown" : type;
                if (key) {
                  defineKeyPropWarningGetter(props, displayName);
                }
                if (ref) {
                  defineRefPropWarningGetter(props, displayName);
                }
              }
            }
            return ReactElement(type, key, ref, self, source, ReactCurrentOwner.current, props);
          }
          function cloneAndReplaceKey(oldElement, newKey) {
            var newElement = ReactElement(oldElement.type, newKey, oldElement.ref, oldElement._self, oldElement._source, oldElement._owner, oldElement.props);
            return newElement;
          }
          function cloneElement(element, config, children) {
            if (element === null || element === void 0) {
              throw new Error("React.cloneElement(...): The argument must be a React element, but you passed " + element + ".");
            }
            var propName;
            var props = assign({}, element.props);
            var key = element.key;
            var ref = element.ref;
            var self = element._self;
            var source = element._source;
            var owner = element._owner;
            if (config != null) {
              if (hasValidRef(config)) {
                ref = config.ref;
                owner = ReactCurrentOwner.current;
              }
              if (hasValidKey(config)) {
                {
                  checkKeyStringCoercion(config.key);
                }
                key = "" + config.key;
              }
              var defaultProps;
              if (element.type && element.type.defaultProps) {
                defaultProps = element.type.defaultProps;
              }
              for (propName in config) {
                if (hasOwnProperty.call(config, propName) && !RESERVED_PROPS.hasOwnProperty(propName)) {
                  if (config[propName] === void 0 && defaultProps !== void 0) {
                    props[propName] = defaultProps[propName];
                  } else {
                    props[propName] = config[propName];
                  }
                }
              }
            }
            var childrenLength = arguments.length - 2;
            if (childrenLength === 1) {
              props.children = children;
            } else if (childrenLength > 1) {
              var childArray = Array(childrenLength);
              for (var i = 0; i < childrenLength; i++) {
                childArray[i] = arguments[i + 2];
              }
              props.children = childArray;
            }
            return ReactElement(element.type, key, ref, self, source, owner, props);
          }
          function isValidElement(object) {
            return typeof object === "object" && object !== null && object.$$typeof === REACT_ELEMENT_TYPE;
          }
          var SEPARATOR = ".";
          var SUBSEPARATOR = ":";
          function escape(key) {
            var escapeRegex = /[=:]/g;
            var escaperLookup = {
              "=": "=0",
              ":": "=2"
            };
            var escapedString = key.replace(escapeRegex, function(match) {
              return escaperLookup[match];
            });
            return "$" + escapedString;
          }
          var didWarnAboutMaps = false;
          var userProvidedKeyEscapeRegex = /\/+/g;
          function escapeUserProvidedKey(text) {
            return text.replace(userProvidedKeyEscapeRegex, "$&/");
          }
          function getElementKey(element, index) {
            if (typeof element === "object" && element !== null && element.key != null) {
              {
                checkKeyStringCoercion(element.key);
              }
              return escape("" + element.key);
            }
            return index.toString(36);
          }
          function mapIntoArray(children, array, escapedPrefix, nameSoFar, callback) {
            var type = typeof children;
            if (type === "undefined" || type === "boolean") {
              children = null;
            }
            var invokeCallback = false;
            if (children === null) {
              invokeCallback = true;
            } else {
              switch (type) {
                case "string":
                case "number":
                  invokeCallback = true;
                  break;
                case "object":
                  switch (children.$$typeof) {
                    case REACT_ELEMENT_TYPE:
                    case REACT_PORTAL_TYPE:
                      invokeCallback = true;
                  }
              }
            }
            if (invokeCallback) {
              var _child = children;
              var mappedChild = callback(_child);
              var childKey = nameSoFar === "" ? SEPARATOR + getElementKey(_child, 0) : nameSoFar;
              if (isArray(mappedChild)) {
                var escapedChildKey = "";
                if (childKey != null) {
                  escapedChildKey = escapeUserProvidedKey(childKey) + "/";
                }
                mapIntoArray(mappedChild, array, escapedChildKey, "", function(c) {
                  return c;
                });
              } else if (mappedChild != null) {
                if (isValidElement(mappedChild)) {
                  {
                    if (mappedChild.key && (!_child || _child.key !== mappedChild.key)) {
                      checkKeyStringCoercion(mappedChild.key);
                    }
                  }
                  mappedChild = cloneAndReplaceKey(
                    mappedChild,
                    // Keep both the (mapped) and old keys if they differ, just as
                    // traverseAllChildren used to do for objects as children
                    escapedPrefix + // $FlowFixMe Flow incorrectly thinks React.Portal doesn't have a key
                    (mappedChild.key && (!_child || _child.key !== mappedChild.key) ? (
                      // $FlowFixMe Flow incorrectly thinks existing element's key can be a number
                      // eslint-disable-next-line react-internal/safe-string-coercion
                      escapeUserProvidedKey("" + mappedChild.key) + "/"
                    ) : "") + childKey
                  );
                }
                array.push(mappedChild);
              }
              return 1;
            }
            var child;
            var nextName;
            var subtreeCount = 0;
            var nextNamePrefix = nameSoFar === "" ? SEPARATOR : nameSoFar + SUBSEPARATOR;
            if (isArray(children)) {
              for (var i = 0; i < children.length; i++) {
                child = children[i];
                nextName = nextNamePrefix + getElementKey(child, i);
                subtreeCount += mapIntoArray(child, array, escapedPrefix, nextName, callback);
              }
            } else {
              var iteratorFn = getIteratorFn(children);
              if (typeof iteratorFn === "function") {
                var iterableChildren = children;
                {
                  if (iteratorFn === iterableChildren.entries) {
                    if (!didWarnAboutMaps) {
                      warn("Using Maps as children is not supported. Use an array of keyed ReactElements instead.");
                    }
                    didWarnAboutMaps = true;
                  }
                }
                var iterator = iteratorFn.call(iterableChildren);
                var step;
                var ii = 0;
                while (!(step = iterator.next()).done) {
                  child = step.value;
                  nextName = nextNamePrefix + getElementKey(child, ii++);
                  subtreeCount += mapIntoArray(child, array, escapedPrefix, nextName, callback);
                }
              } else if (type === "object") {
                var childrenString = String(children);
                throw new Error("Objects are not valid as a React child (found: " + (childrenString === "[object Object]" ? "object with keys {" + Object.keys(children).join(", ") + "}" : childrenString) + "). If you meant to render a collection of children, use an array instead.");
              }
            }
            return subtreeCount;
          }
          function mapChildren(children, func, context) {
            if (children == null) {
              return children;
            }
            var result = [];
            var count = 0;
            mapIntoArray(children, result, "", "", function(child) {
              return func.call(context, child, count++);
            });
            return result;
          }
          function countChildren(children) {
            var n = 0;
            mapChildren(children, function() {
              n++;
            });
            return n;
          }
          function forEachChildren(children, forEachFunc, forEachContext) {
            mapChildren(children, function() {
              forEachFunc.apply(this, arguments);
            }, forEachContext);
          }
          function toArray(children) {
            return mapChildren(children, function(child) {
              return child;
            }) || [];
          }
          function onlyChild(children) {
            if (!isValidElement(children)) {
              throw new Error("React.Children.only expected to receive a single React element child.");
            }
            return children;
          }
          function createContext(defaultValue) {
            var context = {
              $$typeof: REACT_CONTEXT_TYPE,
              // As a workaround to support multiple concurrent renderers, we categorize
              // some renderers as primary and others as secondary. We only expect
              // there to be two concurrent renderers at most: React Native (primary) and
              // Fabric (secondary); React DOM (primary) and React ART (secondary).
              // Secondary renderers store their context values on separate fields.
              _currentValue: defaultValue,
              _currentValue2: defaultValue,
              // Used to track how many concurrent renderers this context currently
              // supports within in a single renderer. Such as parallel server rendering.
              _threadCount: 0,
              // These are circular
              Provider: null,
              Consumer: null,
              // Add these to use same hidden class in VM as ServerContext
              _defaultValue: null,
              _globalName: null
            };
            context.Provider = {
              $$typeof: REACT_PROVIDER_TYPE,
              _context: context
            };
            var hasWarnedAboutUsingNestedContextConsumers = false;
            var hasWarnedAboutUsingConsumerProvider = false;
            var hasWarnedAboutDisplayNameOnConsumer = false;
            {
              var Consumer = {
                $$typeof: REACT_CONTEXT_TYPE,
                _context: context
              };
              Object.defineProperties(Consumer, {
                Provider: {
                  get: function() {
                    if (!hasWarnedAboutUsingConsumerProvider) {
                      hasWarnedAboutUsingConsumerProvider = true;
                      error("Rendering <Context.Consumer.Provider> is not supported and will be removed in a future major release. Did you mean to render <Context.Provider> instead?");
                    }
                    return context.Provider;
                  },
                  set: function(_Provider) {
                    context.Provider = _Provider;
                  }
                },
                _currentValue: {
                  get: function() {
                    return context._currentValue;
                  },
                  set: function(_currentValue) {
                    context._currentValue = _currentValue;
                  }
                },
                _currentValue2: {
                  get: function() {
                    return context._currentValue2;
                  },
                  set: function(_currentValue2) {
                    context._currentValue2 = _currentValue2;
                  }
                },
                _threadCount: {
                  get: function() {
                    return context._threadCount;
                  },
                  set: function(_threadCount) {
                    context._threadCount = _threadCount;
                  }
                },
                Consumer: {
                  get: function() {
                    if (!hasWarnedAboutUsingNestedContextConsumers) {
                      hasWarnedAboutUsingNestedContextConsumers = true;
                      error("Rendering <Context.Consumer.Consumer> is not supported and will be removed in a future major release. Did you mean to render <Context.Consumer> instead?");
                    }
                    return context.Consumer;
                  }
                },
                displayName: {
                  get: function() {
                    return context.displayName;
                  },
                  set: function(displayName) {
                    if (!hasWarnedAboutDisplayNameOnConsumer) {
                      warn("Setting `displayName` on Context.Consumer has no effect. You should set it directly on the context with Context.displayName = '%s'.", displayName);
                      hasWarnedAboutDisplayNameOnConsumer = true;
                    }
                  }
                }
              });
              context.Consumer = Consumer;
            }
            {
              context._currentRenderer = null;
              context._currentRenderer2 = null;
            }
            return context;
          }
          var Uninitialized = -1;
          var Pending = 0;
          var Resolved = 1;
          var Rejected = 2;
          function lazyInitializer(payload) {
            if (payload._status === Uninitialized) {
              var ctor = payload._result;
              var thenable = ctor();
              thenable.then(function(moduleObject2) {
                if (payload._status === Pending || payload._status === Uninitialized) {
                  var resolved = payload;
                  resolved._status = Resolved;
                  resolved._result = moduleObject2;
                }
              }, function(error2) {
                if (payload._status === Pending || payload._status === Uninitialized) {
                  var rejected = payload;
                  rejected._status = Rejected;
                  rejected._result = error2;
                }
              });
              if (payload._status === Uninitialized) {
                var pending = payload;
                pending._status = Pending;
                pending._result = thenable;
              }
            }
            if (payload._status === Resolved) {
              var moduleObject = payload._result;
              {
                if (moduleObject === void 0) {
                  error("lazy: Expected the result of a dynamic import() call. Instead received: %s\n\nYour code should look like: \n  const MyComponent = lazy(() => import('./MyComponent'))\n\nDid you accidentally put curly braces around the import?", moduleObject);
                }
              }
              {
                if (!("default" in moduleObject)) {
                  error("lazy: Expected the result of a dynamic import() call. Instead received: %s\n\nYour code should look like: \n  const MyComponent = lazy(() => import('./MyComponent'))", moduleObject);
                }
              }
              return moduleObject.default;
            } else {
              throw payload._result;
            }
          }
          function lazy(ctor) {
            var payload = {
              // We use these fields to store the result.
              _status: Uninitialized,
              _result: ctor
            };
            var lazyType = {
              $$typeof: REACT_LAZY_TYPE,
              _payload: payload,
              _init: lazyInitializer
            };
            {
              var defaultProps;
              var propTypes;
              Object.defineProperties(lazyType, {
                defaultProps: {
                  configurable: true,
                  get: function() {
                    return defaultProps;
                  },
                  set: function(newDefaultProps) {
                    error("React.lazy(...): It is not supported to assign `defaultProps` to a lazy component import. Either specify them where the component is defined, or create a wrapping component around it.");
                    defaultProps = newDefaultProps;
                    Object.defineProperty(lazyType, "defaultProps", {
                      enumerable: true
                    });
                  }
                },
                propTypes: {
                  configurable: true,
                  get: function() {
                    return propTypes;
                  },
                  set: function(newPropTypes) {
                    error("React.lazy(...): It is not supported to assign `propTypes` to a lazy component import. Either specify them where the component is defined, or create a wrapping component around it.");
                    propTypes = newPropTypes;
                    Object.defineProperty(lazyType, "propTypes", {
                      enumerable: true
                    });
                  }
                }
              });
            }
            return lazyType;
          }
          function forwardRef(render) {
            {
              if (render != null && render.$$typeof === REACT_MEMO_TYPE) {
                error("forwardRef requires a render function but received a `memo` component. Instead of forwardRef(memo(...)), use memo(forwardRef(...)).");
              } else if (typeof render !== "function") {
                error("forwardRef requires a render function but was given %s.", render === null ? "null" : typeof render);
              } else {
                if (render.length !== 0 && render.length !== 2) {
                  error("forwardRef render functions accept exactly two parameters: props and ref. %s", render.length === 1 ? "Did you forget to use the ref parameter?" : "Any additional parameter will be undefined.");
                }
              }
              if (render != null) {
                if (render.defaultProps != null || render.propTypes != null) {
                  error("forwardRef render functions do not support propTypes or defaultProps. Did you accidentally pass a React component?");
                }
              }
            }
            var elementType = {
              $$typeof: REACT_FORWARD_REF_TYPE,
              render
            };
            {
              var ownName;
              Object.defineProperty(elementType, "displayName", {
                enumerable: false,
                configurable: true,
                get: function() {
                  return ownName;
                },
                set: function(name) {
                  ownName = name;
                  if (!render.name && !render.displayName) {
                    render.displayName = name;
                  }
                }
              });
            }
            return elementType;
          }
          var REACT_MODULE_REFERENCE;
          {
            REACT_MODULE_REFERENCE = Symbol.for("react.module.reference");
          }
          function isValidElementType(type) {
            if (typeof type === "string" || typeof type === "function") {
              return true;
            }
            if (type === REACT_FRAGMENT_TYPE || type === REACT_PROFILER_TYPE || enableDebugTracing || type === REACT_STRICT_MODE_TYPE || type === REACT_SUSPENSE_TYPE || type === REACT_SUSPENSE_LIST_TYPE || enableLegacyHidden || type === REACT_OFFSCREEN_TYPE || enableScopeAPI || enableCacheElement || enableTransitionTracing) {
              return true;
            }
            if (typeof type === "object" && type !== null) {
              if (type.$$typeof === REACT_LAZY_TYPE || type.$$typeof === REACT_MEMO_TYPE || type.$$typeof === REACT_PROVIDER_TYPE || type.$$typeof === REACT_CONTEXT_TYPE || type.$$typeof === REACT_FORWARD_REF_TYPE || // This needs to include all possible module reference object
              // types supported by any Flight configuration anywhere since
              // we don't know which Flight build this will end up being used
              // with.
              type.$$typeof === REACT_MODULE_REFERENCE || type.getModuleId !== void 0) {
                return true;
              }
            }
            return false;
          }
          function memo(type, compare) {
            {
              if (!isValidElementType(type)) {
                error("memo: The first argument must be a component. Instead received: %s", type === null ? "null" : typeof type);
              }
            }
            var elementType = {
              $$typeof: REACT_MEMO_TYPE,
              type,
              compare: compare === void 0 ? null : compare
            };
            {
              var ownName;
              Object.defineProperty(elementType, "displayName", {
                enumerable: false,
                configurable: true,
                get: function() {
                  return ownName;
                },
                set: function(name) {
                  ownName = name;
                  if (!type.name && !type.displayName) {
                    type.displayName = name;
                  }
                }
              });
            }
            return elementType;
          }
          function resolveDispatcher() {
            var dispatcher = ReactCurrentDispatcher.current;
            {
              if (dispatcher === null) {
                error("Invalid hook call. Hooks can only be called inside of the body of a function component. This could happen for one of the following reasons:\n1. You might have mismatching versions of React and the renderer (such as React DOM)\n2. You might be breaking the Rules of Hooks\n3. You might have more than one copy of React in the same app\nSee https://reactjs.org/link/invalid-hook-call for tips about how to debug and fix this problem.");
              }
            }
            return dispatcher;
          }
          function useContext(Context) {
            var dispatcher = resolveDispatcher();
            {
              if (Context._context !== void 0) {
                var realContext = Context._context;
                if (realContext.Consumer === Context) {
                  error("Calling useContext(Context.Consumer) is not supported, may cause bugs, and will be removed in a future major release. Did you mean to call useContext(Context) instead?");
                } else if (realContext.Provider === Context) {
                  error("Calling useContext(Context.Provider) is not supported. Did you mean to call useContext(Context) instead?");
                }
              }
            }
            return dispatcher.useContext(Context);
          }
          function useState(initialState) {
            var dispatcher = resolveDispatcher();
            return dispatcher.useState(initialState);
          }
          function useReducer(reducer, initialArg, init) {
            var dispatcher = resolveDispatcher();
            return dispatcher.useReducer(reducer, initialArg, init);
          }
          function useRef(initialValue) {
            var dispatcher = resolveDispatcher();
            return dispatcher.useRef(initialValue);
          }
          function useEffect(create2, deps) {
            var dispatcher = resolveDispatcher();
            return dispatcher.useEffect(create2, deps);
          }
          function useInsertionEffect(create2, deps) {
            var dispatcher = resolveDispatcher();
            return dispatcher.useInsertionEffect(create2, deps);
          }
          function useLayoutEffect(create2, deps) {
            var dispatcher = resolveDispatcher();
            return dispatcher.useLayoutEffect(create2, deps);
          }
          function useCallback(callback, deps) {
            var dispatcher = resolveDispatcher();
            return dispatcher.useCallback(callback, deps);
          }
          function useMemo(create2, deps) {
            var dispatcher = resolveDispatcher();
            return dispatcher.useMemo(create2, deps);
          }
          function useImperativeHandle(ref, create2, deps) {
            var dispatcher = resolveDispatcher();
            return dispatcher.useImperativeHandle(ref, create2, deps);
          }
          function useDebugValue(value, formatterFn) {
            {
              var dispatcher = resolveDispatcher();
              return dispatcher.useDebugValue(value, formatterFn);
            }
          }
          function useTransition() {
            var dispatcher = resolveDispatcher();
            return dispatcher.useTransition();
          }
          function useDeferredValue(value) {
            var dispatcher = resolveDispatcher();
            return dispatcher.useDeferredValue(value);
          }
          function useId() {
            var dispatcher = resolveDispatcher();
            return dispatcher.useId();
          }
          function useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot) {
            var dispatcher = resolveDispatcher();
            return dispatcher.useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot);
          }
          var disabledDepth = 0;
          var prevLog;
          var prevInfo;
          var prevWarn;
          var prevError;
          var prevGroup;
          var prevGroupCollapsed;
          var prevGroupEnd;
          function disabledLog() {
          }
          disabledLog.__reactDisabledLog = true;
          function disableLogs() {
            {
              if (disabledDepth === 0) {
                prevLog = console.log;
                prevInfo = console.info;
                prevWarn = console.warn;
                prevError = console.error;
                prevGroup = console.group;
                prevGroupCollapsed = console.groupCollapsed;
                prevGroupEnd = console.groupEnd;
                var props = {
                  configurable: true,
                  enumerable: true,
                  value: disabledLog,
                  writable: true
                };
                Object.defineProperties(console, {
                  info: props,
                  log: props,
                  warn: props,
                  error: props,
                  group: props,
                  groupCollapsed: props,
                  groupEnd: props
                });
              }
              disabledDepth++;
            }
          }
          function reenableLogs() {
            {
              disabledDepth--;
              if (disabledDepth === 0) {
                var props = {
                  configurable: true,
                  enumerable: true,
                  writable: true
                };
                Object.defineProperties(console, {
                  log: assign({}, props, {
                    value: prevLog
                  }),
                  info: assign({}, props, {
                    value: prevInfo
                  }),
                  warn: assign({}, props, {
                    value: prevWarn
                  }),
                  error: assign({}, props, {
                    value: prevError
                  }),
                  group: assign({}, props, {
                    value: prevGroup
                  }),
                  groupCollapsed: assign({}, props, {
                    value: prevGroupCollapsed
                  }),
                  groupEnd: assign({}, props, {
                    value: prevGroupEnd
                  })
                });
              }
              if (disabledDepth < 0) {
                error("disabledDepth fell below zero. This is a bug in React. Please file an issue.");
              }
            }
          }
          var ReactCurrentDispatcher$1 = ReactSharedInternals.ReactCurrentDispatcher;
          var prefix;
          function describeBuiltInComponentFrame(name, source, ownerFn) {
            {
              if (prefix === void 0) {
                try {
                  throw Error();
                } catch (x) {
                  var match = x.stack.trim().match(/\n( *(at )?)/);
                  prefix = match && match[1] || "";
                }
              }
              return "\n" + prefix + name;
            }
          }
          var reentry = false;
          var componentFrameCache;
          {
            var PossiblyWeakMap = typeof WeakMap === "function" ? WeakMap : Map;
            componentFrameCache = new PossiblyWeakMap();
          }
          function describeNativeComponentFrame(fn, construct) {
            if (!fn || reentry) {
              return "";
            }
            {
              var frame = componentFrameCache.get(fn);
              if (frame !== void 0) {
                return frame;
              }
            }
            var control;
            reentry = true;
            var previousPrepareStackTrace = Error.prepareStackTrace;
            Error.prepareStackTrace = void 0;
            var previousDispatcher;
            {
              previousDispatcher = ReactCurrentDispatcher$1.current;
              ReactCurrentDispatcher$1.current = null;
              disableLogs();
            }
            try {
              if (construct) {
                var Fake = function() {
                  throw Error();
                };
                Object.defineProperty(Fake.prototype, "props", {
                  set: function() {
                    throw Error();
                  }
                });
                if (typeof Reflect === "object" && Reflect.construct) {
                  try {
                    Reflect.construct(Fake, []);
                  } catch (x) {
                    control = x;
                  }
                  Reflect.construct(fn, [], Fake);
                } else {
                  try {
                    Fake.call();
                  } catch (x) {
                    control = x;
                  }
                  fn.call(Fake.prototype);
                }
              } else {
                try {
                  throw Error();
                } catch (x) {
                  control = x;
                }
                fn();
              }
            } catch (sample) {
              if (sample && control && typeof sample.stack === "string") {
                var sampleLines = sample.stack.split("\n");
                var controlLines = control.stack.split("\n");
                var s = sampleLines.length - 1;
                var c = controlLines.length - 1;
                while (s >= 1 && c >= 0 && sampleLines[s] !== controlLines[c]) {
                  c--;
                }
                for (; s >= 1 && c >= 0; s--, c--) {
                  if (sampleLines[s] !== controlLines[c]) {
                    if (s !== 1 || c !== 1) {
                      do {
                        s--;
                        c--;
                        if (c < 0 || sampleLines[s] !== controlLines[c]) {
                          var _frame = "\n" + sampleLines[s].replace(" at new ", " at ");
                          if (fn.displayName && _frame.includes("<anonymous>")) {
                            _frame = _frame.replace("<anonymous>", fn.displayName);
                          }
                          {
                            if (typeof fn === "function") {
                              componentFrameCache.set(fn, _frame);
                            }
                          }
                          return _frame;
                        }
                      } while (s >= 1 && c >= 0);
                    }
                    break;
                  }
                }
              }
            } finally {
              reentry = false;
              {
                ReactCurrentDispatcher$1.current = previousDispatcher;
                reenableLogs();
              }
              Error.prepareStackTrace = previousPrepareStackTrace;
            }
            var name = fn ? fn.displayName || fn.name : "";
            var syntheticFrame = name ? describeBuiltInComponentFrame(name) : "";
            {
              if (typeof fn === "function") {
                componentFrameCache.set(fn, syntheticFrame);
              }
            }
            return syntheticFrame;
          }
          function describeFunctionComponentFrame(fn, source, ownerFn) {
            {
              return describeNativeComponentFrame(fn, false);
            }
          }
          function shouldConstruct(Component2) {
            var prototype = Component2.prototype;
            return !!(prototype && prototype.isReactComponent);
          }
          function describeUnknownElementTypeFrameInDEV(type, source, ownerFn) {
            if (type == null) {
              return "";
            }
            if (typeof type === "function") {
              {
                return describeNativeComponentFrame(type, shouldConstruct(type));
              }
            }
            if (typeof type === "string") {
              return describeBuiltInComponentFrame(type);
            }
            switch (type) {
              case REACT_SUSPENSE_TYPE:
                return describeBuiltInComponentFrame("Suspense");
              case REACT_SUSPENSE_LIST_TYPE:
                return describeBuiltInComponentFrame("SuspenseList");
            }
            if (typeof type === "object") {
              switch (type.$$typeof) {
                case REACT_FORWARD_REF_TYPE:
                  return describeFunctionComponentFrame(type.render);
                case REACT_MEMO_TYPE:
                  return describeUnknownElementTypeFrameInDEV(type.type, source, ownerFn);
                case REACT_LAZY_TYPE: {
                  var lazyComponent = type;
                  var payload = lazyComponent._payload;
                  var init = lazyComponent._init;
                  try {
                    return describeUnknownElementTypeFrameInDEV(init(payload), source, ownerFn);
                  } catch (x) {
                  }
                }
              }
            }
            return "";
          }
          var loggedTypeFailures = {};
          var ReactDebugCurrentFrame$1 = ReactSharedInternals.ReactDebugCurrentFrame;
          function setCurrentlyValidatingElement(element) {
            {
              if (element) {
                var owner = element._owner;
                var stack = describeUnknownElementTypeFrameInDEV(element.type, element._source, owner ? owner.type : null);
                ReactDebugCurrentFrame$1.setExtraStackFrame(stack);
              } else {
                ReactDebugCurrentFrame$1.setExtraStackFrame(null);
              }
            }
          }
          function checkPropTypes(typeSpecs, values, location, componentName, element) {
            {
              var has = Function.call.bind(hasOwnProperty);
              for (var typeSpecName in typeSpecs) {
                if (has(typeSpecs, typeSpecName)) {
                  var error$1 = void 0;
                  try {
                    if (typeof typeSpecs[typeSpecName] !== "function") {
                      var err = Error((componentName || "React class") + ": " + location + " type `" + typeSpecName + "` is invalid; it must be a function, usually from the `prop-types` package, but received `" + typeof typeSpecs[typeSpecName] + "`.This often happens because of typos such as `PropTypes.function` instead of `PropTypes.func`.");
                      err.name = "Invariant Violation";
                      throw err;
                    }
                    error$1 = typeSpecs[typeSpecName](values, typeSpecName, componentName, location, null, "SECRET_DO_NOT_PASS_THIS_OR_YOU_WILL_BE_FIRED");
                  } catch (ex) {
                    error$1 = ex;
                  }
                  if (error$1 && !(error$1 instanceof Error)) {
                    setCurrentlyValidatingElement(element);
                    error("%s: type specification of %s `%s` is invalid; the type checker function must return `null` or an `Error` but returned a %s. You may have forgotten to pass an argument to the type checker creator (arrayOf, instanceOf, objectOf, oneOf, oneOfType, and shape all require an argument).", componentName || "React class", location, typeSpecName, typeof error$1);
                    setCurrentlyValidatingElement(null);
                  }
                  if (error$1 instanceof Error && !(error$1.message in loggedTypeFailures)) {
                    loggedTypeFailures[error$1.message] = true;
                    setCurrentlyValidatingElement(element);
                    error("Failed %s type: %s", location, error$1.message);
                    setCurrentlyValidatingElement(null);
                  }
                }
              }
            }
          }
          function setCurrentlyValidatingElement$1(element) {
            {
              if (element) {
                var owner = element._owner;
                var stack = describeUnknownElementTypeFrameInDEV(element.type, element._source, owner ? owner.type : null);
                setExtraStackFrame(stack);
              } else {
                setExtraStackFrame(null);
              }
            }
          }
          var propTypesMisspellWarningShown;
          {
            propTypesMisspellWarningShown = false;
          }
          function getDeclarationErrorAddendum() {
            if (ReactCurrentOwner.current) {
              var name = getComponentNameFromType(ReactCurrentOwner.current.type);
              if (name) {
                return "\n\nCheck the render method of `" + name + "`.";
              }
            }
            return "";
          }
          function getSourceInfoErrorAddendum(source) {
            if (source !== void 0) {
              var fileName = source.fileName.replace(/^.*[\\\/]/, "");
              var lineNumber = source.lineNumber;
              return "\n\nCheck your code at " + fileName + ":" + lineNumber + ".";
            }
            return "";
          }
          function getSourceInfoErrorAddendumForProps(elementProps) {
            if (elementProps !== null && elementProps !== void 0) {
              return getSourceInfoErrorAddendum(elementProps.__source);
            }
            return "";
          }
          var ownerHasKeyUseWarning = {};
          function getCurrentComponentErrorInfo(parentType) {
            var info = getDeclarationErrorAddendum();
            if (!info) {
              var parentName = typeof parentType === "string" ? parentType : parentType.displayName || parentType.name;
              if (parentName) {
                info = "\n\nCheck the top-level render call using <" + parentName + ">.";
              }
            }
            return info;
          }
          function validateExplicitKey(element, parentType) {
            if (!element._store || element._store.validated || element.key != null) {
              return;
            }
            element._store.validated = true;
            var currentComponentErrorInfo = getCurrentComponentErrorInfo(parentType);
            if (ownerHasKeyUseWarning[currentComponentErrorInfo]) {
              return;
            }
            ownerHasKeyUseWarning[currentComponentErrorInfo] = true;
            var childOwner = "";
            if (element && element._owner && element._owner !== ReactCurrentOwner.current) {
              childOwner = " It was passed a child from " + getComponentNameFromType(element._owner.type) + ".";
            }
            {
              setCurrentlyValidatingElement$1(element);
              error('Each child in a list should have a unique "key" prop.%s%s See https://reactjs.org/link/warning-keys for more information.', currentComponentErrorInfo, childOwner);
              setCurrentlyValidatingElement$1(null);
            }
          }
          function validateChildKeys(node, parentType) {
            if (typeof node !== "object") {
              return;
            }
            if (isArray(node)) {
              for (var i = 0; i < node.length; i++) {
                var child = node[i];
                if (isValidElement(child)) {
                  validateExplicitKey(child, parentType);
                }
              }
            } else if (isValidElement(node)) {
              if (node._store) {
                node._store.validated = true;
              }
            } else if (node) {
              var iteratorFn = getIteratorFn(node);
              if (typeof iteratorFn === "function") {
                if (iteratorFn !== node.entries) {
                  var iterator = iteratorFn.call(node);
                  var step;
                  while (!(step = iterator.next()).done) {
                    if (isValidElement(step.value)) {
                      validateExplicitKey(step.value, parentType);
                    }
                  }
                }
              }
            }
          }
          function validatePropTypes(element) {
            {
              var type = element.type;
              if (type === null || type === void 0 || typeof type === "string") {
                return;
              }
              var propTypes;
              if (typeof type === "function") {
                propTypes = type.propTypes;
              } else if (typeof type === "object" && (type.$$typeof === REACT_FORWARD_REF_TYPE || // Note: Memo only checks outer props here.
              // Inner props are checked in the reconciler.
              type.$$typeof === REACT_MEMO_TYPE)) {
                propTypes = type.propTypes;
              } else {
                return;
              }
              if (propTypes) {
                var name = getComponentNameFromType(type);
                checkPropTypes(propTypes, element.props, "prop", name, element);
              } else if (type.PropTypes !== void 0 && !propTypesMisspellWarningShown) {
                propTypesMisspellWarningShown = true;
                var _name = getComponentNameFromType(type);
                error("Component %s declared `PropTypes` instead of `propTypes`. Did you misspell the property assignment?", _name || "Unknown");
              }
              if (typeof type.getDefaultProps === "function" && !type.getDefaultProps.isReactClassApproved) {
                error("getDefaultProps is only used on classic React.createClass definitions. Use a static property named `defaultProps` instead.");
              }
            }
          }
          function validateFragmentProps(fragment) {
            {
              var keys = Object.keys(fragment.props);
              for (var i = 0; i < keys.length; i++) {
                var key = keys[i];
                if (key !== "children" && key !== "key") {
                  setCurrentlyValidatingElement$1(fragment);
                  error("Invalid prop `%s` supplied to `React.Fragment`. React.Fragment can only have `key` and `children` props.", key);
                  setCurrentlyValidatingElement$1(null);
                  break;
                }
              }
              if (fragment.ref !== null) {
                setCurrentlyValidatingElement$1(fragment);
                error("Invalid attribute `ref` supplied to `React.Fragment`.");
                setCurrentlyValidatingElement$1(null);
              }
            }
          }
          function createElementWithValidation(type, props, children) {
            var validType = isValidElementType(type);
            if (!validType) {
              var info = "";
              if (type === void 0 || typeof type === "object" && type !== null && Object.keys(type).length === 0) {
                info += " You likely forgot to export your component from the file it's defined in, or you might have mixed up default and named imports.";
              }
              var sourceInfo = getSourceInfoErrorAddendumForProps(props);
              if (sourceInfo) {
                info += sourceInfo;
              } else {
                info += getDeclarationErrorAddendum();
              }
              var typeString;
              if (type === null) {
                typeString = "null";
              } else if (isArray(type)) {
                typeString = "array";
              } else if (type !== void 0 && type.$$typeof === REACT_ELEMENT_TYPE) {
                typeString = "<" + (getComponentNameFromType(type.type) || "Unknown") + " />";
                info = " Did you accidentally export a JSX literal instead of a component?";
              } else {
                typeString = typeof type;
              }
              {
                error("React.createElement: type is invalid -- expected a string (for built-in components) or a class/function (for composite components) but got: %s.%s", typeString, info);
              }
            }
            var element = createElement.apply(this, arguments);
            if (element == null) {
              return element;
            }
            if (validType) {
              for (var i = 2; i < arguments.length; i++) {
                validateChildKeys(arguments[i], type);
              }
            }
            if (type === REACT_FRAGMENT_TYPE) {
              validateFragmentProps(element);
            } else {
              validatePropTypes(element);
            }
            return element;
          }
          var didWarnAboutDeprecatedCreateFactory = false;
          function createFactoryWithValidation(type) {
            var validatedFactory = createElementWithValidation.bind(null, type);
            validatedFactory.type = type;
            {
              if (!didWarnAboutDeprecatedCreateFactory) {
                didWarnAboutDeprecatedCreateFactory = true;
                warn("React.createFactory() is deprecated and will be removed in a future major release. Consider using JSX or use React.createElement() directly instead.");
              }
              Object.defineProperty(validatedFactory, "type", {
                enumerable: false,
                get: function() {
                  warn("Factory.type is deprecated. Access the class directly before passing it to createFactory.");
                  Object.defineProperty(this, "type", {
                    value: type
                  });
                  return type;
                }
              });
            }
            return validatedFactory;
          }
          function cloneElementWithValidation(element, props, children) {
            var newElement = cloneElement.apply(this, arguments);
            for (var i = 2; i < arguments.length; i++) {
              validateChildKeys(arguments[i], newElement.type);
            }
            validatePropTypes(newElement);
            return newElement;
          }
          function startTransition(scope, options) {
            var prevTransition = ReactCurrentBatchConfig.transition;
            ReactCurrentBatchConfig.transition = {};
            var currentTransition = ReactCurrentBatchConfig.transition;
            {
              ReactCurrentBatchConfig.transition._updatedFibers = /* @__PURE__ */ new Set();
            }
            try {
              scope();
            } finally {
              ReactCurrentBatchConfig.transition = prevTransition;
              {
                if (prevTransition === null && currentTransition._updatedFibers) {
                  var updatedFibersCount = currentTransition._updatedFibers.size;
                  if (updatedFibersCount > 10) {
                    warn("Detected a large number of updates inside startTransition. If this is due to a subscription please re-write it to use React provided hooks. Otherwise concurrent mode guarantees are off the table.");
                  }
                  currentTransition._updatedFibers.clear();
                }
              }
            }
          }
          var didWarnAboutMessageChannel = false;
          var enqueueTaskImpl = null;
          function enqueueTask(task) {
            if (enqueueTaskImpl === null) {
              try {
                var requireString = ("require" + Math.random()).slice(0, 7);
                var nodeRequire = module && module[requireString];
                enqueueTaskImpl = nodeRequire.call(module, "timers").setImmediate;
              } catch (_err) {
                enqueueTaskImpl = function(callback) {
                  {
                    if (didWarnAboutMessageChannel === false) {
                      didWarnAboutMessageChannel = true;
                      if (typeof MessageChannel === "undefined") {
                        error("This browser does not have a MessageChannel implementation, so enqueuing tasks via await act(async () => ...) will fail. Please file an issue at https://github.com/facebook/react/issues if you encounter this warning.");
                      }
                    }
                  }
                  var channel = new MessageChannel();
                  channel.port1.onmessage = callback;
                  channel.port2.postMessage(void 0);
                };
              }
            }
            return enqueueTaskImpl(task);
          }
          var actScopeDepth = 0;
          var didWarnNoAwaitAct = false;
          function act(callback) {
            {
              var prevActScopeDepth = actScopeDepth;
              actScopeDepth++;
              if (ReactCurrentActQueue.current === null) {
                ReactCurrentActQueue.current = [];
              }
              var prevIsBatchingLegacy = ReactCurrentActQueue.isBatchingLegacy;
              var result;
              try {
                ReactCurrentActQueue.isBatchingLegacy = true;
                result = callback();
                if (!prevIsBatchingLegacy && ReactCurrentActQueue.didScheduleLegacyUpdate) {
                  var queue = ReactCurrentActQueue.current;
                  if (queue !== null) {
                    ReactCurrentActQueue.didScheduleLegacyUpdate = false;
                    flushActQueue(queue);
                  }
                }
              } catch (error2) {
                popActScope(prevActScopeDepth);
                throw error2;
              } finally {
                ReactCurrentActQueue.isBatchingLegacy = prevIsBatchingLegacy;
              }
              if (result !== null && typeof result === "object" && typeof result.then === "function") {
                var thenableResult = result;
                var wasAwaited = false;
                var thenable = {
                  then: function(resolve, reject) {
                    wasAwaited = true;
                    thenableResult.then(function(returnValue2) {
                      popActScope(prevActScopeDepth);
                      if (actScopeDepth === 0) {
                        recursivelyFlushAsyncActWork(returnValue2, resolve, reject);
                      } else {
                        resolve(returnValue2);
                      }
                    }, function(error2) {
                      popActScope(prevActScopeDepth);
                      reject(error2);
                    });
                  }
                };
                {
                  if (!didWarnNoAwaitAct && typeof Promise !== "undefined") {
                    Promise.resolve().then(function() {
                    }).then(function() {
                      if (!wasAwaited) {
                        didWarnNoAwaitAct = true;
                        error("You called act(async () => ...) without await. This could lead to unexpected testing behaviour, interleaving multiple act calls and mixing their scopes. You should - await act(async () => ...);");
                      }
                    });
                  }
                }
                return thenable;
              } else {
                var returnValue = result;
                popActScope(prevActScopeDepth);
                if (actScopeDepth === 0) {
                  var _queue = ReactCurrentActQueue.current;
                  if (_queue !== null) {
                    flushActQueue(_queue);
                    ReactCurrentActQueue.current = null;
                  }
                  var _thenable = {
                    then: function(resolve, reject) {
                      if (ReactCurrentActQueue.current === null) {
                        ReactCurrentActQueue.current = [];
                        recursivelyFlushAsyncActWork(returnValue, resolve, reject);
                      } else {
                        resolve(returnValue);
                      }
                    }
                  };
                  return _thenable;
                } else {
                  var _thenable2 = {
                    then: function(resolve, reject) {
                      resolve(returnValue);
                    }
                  };
                  return _thenable2;
                }
              }
            }
          }
          function popActScope(prevActScopeDepth) {
            {
              if (prevActScopeDepth !== actScopeDepth - 1) {
                error("You seem to have overlapping act() calls, this is not supported. Be sure to await previous act() calls before making a new one. ");
              }
              actScopeDepth = prevActScopeDepth;
            }
          }
          function recursivelyFlushAsyncActWork(returnValue, resolve, reject) {
            {
              var queue = ReactCurrentActQueue.current;
              if (queue !== null) {
                try {
                  flushActQueue(queue);
                  enqueueTask(function() {
                    if (queue.length === 0) {
                      ReactCurrentActQueue.current = null;
                      resolve(returnValue);
                    } else {
                      recursivelyFlushAsyncActWork(returnValue, resolve, reject);
                    }
                  });
                } catch (error2) {
                  reject(error2);
                }
              } else {
                resolve(returnValue);
              }
            }
          }
          var isFlushing = false;
          function flushActQueue(queue) {
            {
              if (!isFlushing) {
                isFlushing = true;
                var i = 0;
                try {
                  for (; i < queue.length; i++) {
                    var callback = queue[i];
                    do {
                      callback = callback(true);
                    } while (callback !== null);
                  }
                  queue.length = 0;
                } catch (error2) {
                  queue = queue.slice(i + 1);
                  throw error2;
                } finally {
                  isFlushing = false;
                }
              }
            }
          }
          var createElement$1 = createElementWithValidation;
          var cloneElement$1 = cloneElementWithValidation;
          var createFactory = createFactoryWithValidation;
          var Children = {
            map: mapChildren,
            forEach: forEachChildren,
            count: countChildren,
            toArray,
            only: onlyChild
          };
          exports.Children = Children;
          exports.Component = Component;
          exports.Fragment = REACT_FRAGMENT_TYPE;
          exports.Profiler = REACT_PROFILER_TYPE;
          exports.PureComponent = PureComponent;
          exports.StrictMode = REACT_STRICT_MODE_TYPE;
          exports.Suspense = REACT_SUSPENSE_TYPE;
          exports.__SECRET_INTERNALS_DO_NOT_USE_OR_YOU_WILL_BE_FIRED = ReactSharedInternals;
          exports.act = act;
          exports.cloneElement = cloneElement$1;
          exports.createContext = createContext;
          exports.createElement = createElement$1;
          exports.createFactory = createFactory;
          exports.createRef = createRef;
          exports.forwardRef = forwardRef;
          exports.isValidElement = isValidElement;
          exports.lazy = lazy;
          exports.memo = memo;
          exports.startTransition = startTransition;
          exports.unstable_act = act;
          exports.useCallback = useCallback;
          exports.useContext = useContext;
          exports.useDebugValue = useDebugValue;
          exports.useDeferredValue = useDeferredValue;
          exports.useEffect = useEffect;
          exports.useId = useId;
          exports.useImperativeHandle = useImperativeHandle;
          exports.useInsertionEffect = useInsertionEffect;
          exports.useLayoutEffect = useLayoutEffect;
          exports.useMemo = useMemo;
          exports.useReducer = useReducer;
          exports.useRef = useRef;
          exports.useState = useState;
          exports.useSyncExternalStore = useSyncExternalStore;
          exports.useTransition = useTransition;
          exports.version = ReactVersion;
          if (typeof __REACT_DEVTOOLS_GLOBAL_HOOK__ !== "undefined" && typeof __REACT_DEVTOOLS_GLOBAL_HOOK__.registerInternalModuleStop === "function") {
            __REACT_DEVTOOLS_GLOBAL_HOOK__.registerInternalModuleStop(new Error());
          }
        })();
      }
    }
  });

  // node_modules/react/index.js
  var require_react = __commonJS({
    "node_modules/react/index.js"(exports, module) {
      "use strict";
      if (false) {
        module.exports = null;
      } else {
        module.exports = require_react_development();
      }
    }
  });

  // node_modules/zustand/esm/vanilla.mjs
  var createStoreImpl = (createState) => {
    let state;
    const listeners = /* @__PURE__ */ new Set();
    const setState = (partial, replace) => {
      const nextState = typeof partial === "function" ? partial(state) : partial;
      if (!Object.is(nextState, state)) {
        const previousState = state;
        state = (replace != null ? replace : typeof nextState !== "object" || nextState === null) ? nextState : Object.assign({}, state, nextState);
        listeners.forEach((listener) => listener(state, previousState));
      }
    };
    const getState = () => state;
    const getInitialState = () => initialState;
    const subscribe = (listener) => {
      listeners.add(listener);
      return () => listeners.delete(listener);
    };
    const api = { setState, getState, getInitialState, subscribe };
    const initialState = state = createState(setState, getState, api);
    return api;
  };
  var createStore = (createState) => createState ? createStoreImpl(createState) : createStoreImpl;

  // node_modules/zustand/esm/react.mjs
  var import_react = __toESM(require_react(), 1);
  var identity = (arg) => arg;
  function useStore(api, selector = identity) {
    const slice = import_react.default.useSyncExternalStore(
      api.subscribe,
      import_react.default.useCallback(() => selector(api.getState()), [api, selector]),
      import_react.default.useCallback(() => selector(api.getInitialState()), [api, selector])
    );
    import_react.default.useDebugValue(slice);
    return slice;
  }
  var createImpl = (createState) => {
    const api = createStore(createState);
    const useBoundStore = (selector) => useStore(api, selector);
    Object.assign(useBoundStore, api);
    return useBoundStore;
  };
  var create = (createState) => createState ? createImpl(createState) : createImpl;

  // node_modules/zustand/esm/middleware.mjs
  function createJSONStorage(getStorage, options) {
    let storage;
    try {
      storage = getStorage();
    } catch (e) {
      return;
    }
    const persistStorage = {
      getItem: (name) => {
        var _a;
        const parse = (str2) => {
          if (str2 === null) {
            return null;
          }
          return JSON.parse(str2, options == null ? void 0 : options.reviver);
        };
        const str = (_a = storage.getItem(name)) != null ? _a : null;
        if (str instanceof Promise) {
          return str.then(parse);
        }
        return parse(str);
      },
      setItem: (name, newValue) => storage.setItem(name, JSON.stringify(newValue, options == null ? void 0 : options.replacer)),
      removeItem: (name) => storage.removeItem(name)
    };
    return persistStorage;
  }
  var toThenable = (fn) => (input) => {
    try {
      const result = fn(input);
      if (result instanceof Promise) {
        return result;
      }
      return {
        then(onFulfilled) {
          return toThenable(onFulfilled)(result);
        },
        catch(_onRejected) {
          return this;
        }
      };
    } catch (e) {
      return {
        then(_onFulfilled) {
          return this;
        },
        catch(onRejected) {
          return toThenable(onRejected)(e);
        }
      };
    }
  };
  var persistImpl = (config, baseOptions) => (set, get, api) => {
    let options = {
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => state,
      version: 0,
      merge: (persistedState, currentState) => ({
        ...currentState,
        ...persistedState
      }),
      ...baseOptions
    };
    let hasHydrated = false;
    const hydrationListeners = /* @__PURE__ */ new Set();
    const finishHydrationListeners = /* @__PURE__ */ new Set();
    let storage = options.storage;
    if (!storage) {
      return config(
        (...args) => {
          console.warn(
            `[zustand persist middleware] Unable to update item '${options.name}', the given storage is currently unavailable.`
          );
          set(...args);
        },
        get,
        api
      );
    }
    const setItem = () => {
      const state = options.partialize({ ...get() });
      return storage.setItem(options.name, {
        state,
        version: options.version
      });
    };
    const savedSetState = api.setState;
    api.setState = (state, replace) => {
      savedSetState(state, replace);
      return setItem();
    };
    const configResult = config(
      (...args) => {
        set(...args);
        return setItem();
      },
      get,
      api
    );
    api.getInitialState = () => configResult;
    let stateFromStorage;
    const hydrate = () => {
      var _a, _b;
      if (!storage) return;
      hasHydrated = false;
      hydrationListeners.forEach((cb) => {
        var _a2;
        return cb((_a2 = get()) != null ? _a2 : configResult);
      });
      const postRehydrationCallback = ((_b = options.onRehydrateStorage) == null ? void 0 : _b.call(options, (_a = get()) != null ? _a : configResult)) || void 0;
      return toThenable(storage.getItem.bind(storage))(options.name).then((deserializedStorageValue) => {
        if (deserializedStorageValue) {
          if (typeof deserializedStorageValue.version === "number" && deserializedStorageValue.version !== options.version) {
            if (options.migrate) {
              const migration = options.migrate(
                deserializedStorageValue.state,
                deserializedStorageValue.version
              );
              if (migration instanceof Promise) {
                return migration.then((result) => [true, result]);
              }
              return [true, migration];
            }
            console.error(
              `State loaded from storage couldn't be migrated since no migrate function was provided`
            );
          } else {
            return [false, deserializedStorageValue.state];
          }
        }
        return [false, void 0];
      }).then((migrationResult) => {
        var _a2;
        const [migrated, migratedState] = migrationResult;
        stateFromStorage = options.merge(
          migratedState,
          (_a2 = get()) != null ? _a2 : configResult
        );
        set(stateFromStorage, true);
        if (migrated) {
          return setItem();
        }
      }).then(() => {
        postRehydrationCallback == null ? void 0 : postRehydrationCallback(stateFromStorage, void 0);
        stateFromStorage = get();
        hasHydrated = true;
        finishHydrationListeners.forEach((cb) => cb(stateFromStorage));
      }).catch((e) => {
        postRehydrationCallback == null ? void 0 : postRehydrationCallback(void 0, e);
      });
    };
    api.persist = {
      setOptions: (newOptions) => {
        options = {
          ...options,
          ...newOptions
        };
        if (newOptions.storage) {
          storage = newOptions.storage;
        }
      },
      clearStorage: () => {
        storage == null ? void 0 : storage.removeItem(options.name);
      },
      getOptions: () => options,
      rehydrate: () => hydrate(),
      hasHydrated: () => hasHydrated,
      onHydrate: (cb) => {
        hydrationListeners.add(cb);
        return () => {
          hydrationListeners.delete(cb);
        };
      },
      onFinishHydration: (cb) => {
        finishHydrationListeners.add(cb);
        return () => {
          finishHydrationListeners.delete(cb);
        };
      }
    };
    if (!options.skipHydration) {
      hydrate();
    }
    return stateFromStorage || configResult;
  };
  var persist = persistImpl;

  // src/lib/id-generator.ts
  function randomHex(length) {
    const bytes = new Uint8Array(Math.ceil(length / 2));
    crypto.getRandomValues(bytes);
    return Array.from(bytes).map((b) => b.toString(16).padStart(2, "0")).join("").slice(0, length);
  }
  function generateId(prefix) {
    return `${prefix}_${randomHex(12)}`;
  }

  // src/lib/toast-store.ts
  var useToastStore = create((set) => ({
    toasts: [],
    addToast: (toast2) => {
      const id = `toast-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
      const newToast = {
        ...toast2,
        id,
        duration: toast2.duration ?? 4e3
      };
      set((state) => ({
        toasts: [...state.toasts, newToast]
      }));
      if (newToast.duration && newToast.duration > 0) {
        setTimeout(() => {
          set((state) => ({
            toasts: state.toasts.filter((t) => t.id !== id)
          }));
        }, newToast.duration);
      }
    },
    removeToast: (id) => set((state) => ({
      toasts: state.toasts.filter((t) => t.id !== id)
    })),
    clearToasts: () => set({ toasts: [] })
  }));
  var toast = {
    success: (message, duration) => useToastStore.getState().addToast({ type: "success", message, duration }),
    error: (message, duration) => useToastStore.getState().addToast({ type: "error", message, duration }),
    warning: (message, duration) => useToastStore.getState().addToast({ type: "warning", message, duration }),
    info: (message, duration) => useToastStore.getState().addToast({ type: "info", message, duration })
  };

  // src/lib/api-v4.ts
  var import_meta = {};
  var API_URL = import_meta.env.VITE_API_URL || "http://localhost:8000";
  function getContainerTypeFromId(id) {
    if (id.startsWith("sess_")) return "session";
    if (id.startsWith("agnt_")) return "agent";
    if (id.startsWith("tool_")) return "tool";
    if (id.startsWith("src_")) return "source";
    return null;
  }
  function isContainerDiveable(type) {
    return type !== "source";
  }
  function getAuthToken() {
    return localStorage.getItem("auth_token") || import_meta.env.VITE_API_TOKEN || "";
  }
  async function apiFetch(path, options = {}) {
    const token = getAuthToken();
    const response = await fetch(`${API_URL}${path}`, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${token}`,
        ...options.headers
      }
    });
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }));
      const message = error.detail || `API error: ${response.status}`;
      if (response.status === 401) {
        toast.error("Authentication failed - please log in again");
      } else if (response.status === 403) {
        toast.error("Permission denied");
      } else if (response.status === 404) {
        toast.error("Resource not found");
      } else {
        toast.error(message);
      }
      throw new Error(message);
    }
    if (response.status === 204) {
      return void 0;
    }
    return response.json();
  }
  async function getUserSession(userId) {
    return apiFetch(`/usersessions/${userId}`);
  }
  async function listWorkspaceResources(userId, resourceType) {
    const params = resourceType ? `?resource_type=${resourceType}` : "";
    const response = await apiFetch(
      `/usersessions/${userId}/resources${params}`
    );
    return response.resources;
  }
  async function addWorkspaceResource(userId, request) {
    return apiFetch(`/usersessions/${userId}/resources`, {
      method: "POST",
      body: JSON.stringify(request)
    });
  }
  async function updateWorkspaceResource(userId, linkId, updates) {
    return apiFetch(`/usersessions/${userId}/resources/${linkId}`, {
      method: "PATCH",
      body: JSON.stringify(updates)
    });
  }
  async function removeWorkspaceResource(userId, linkId) {
    await apiFetch(`/usersessions/${userId}/resources/${linkId}`, {
      method: "DELETE"
    });
  }
  async function listDefinitions(definitionType, options) {
    const params = new URLSearchParams();
    if (options?.tier) params.set("tier", options.tier);
    if (options?.tags?.length) params.set("tags", options.tags.join(","));
    if (options?.search) params.set("search", options.search);
    const queryString = params.toString();
    const path = `/definitions/${definitionType}${queryString ? `?${queryString}` : ""}`;
    const response = await apiFetch(path);
    return response.definitions;
  }
  async function getDefinition(definitionType, definitionId) {
    return apiFetch(`/definitions/${definitionType}/${definitionId}`);
  }
  async function createDefinition(definitionType, request) {
    const result = await apiFetch(
      `/definitions/${definitionType}`,
      {
        method: "POST",
        body: JSON.stringify(request)
      }
    );
    toast.success(`${definitionType} definition created`);
    return result;
  }
  async function updateDefinition(definitionType, definitionId, request) {
    return apiFetch(`/definitions/${definitionType}/${definitionId}`, {
      method: "PATCH",
      body: JSON.stringify(request)
    });
  }
  async function deleteDefinition(definitionType, definitionId) {
    await apiFetch(`/definitions/${definitionType}/${definitionId}`, {
      method: "DELETE"
    });
    toast.success(`${definitionType} definition deleted`);
  }
  async function createSession(request) {
    const result = await apiFetch(`/sessions`, {
      method: "POST",
      body: JSON.stringify(request)
    });
    toast.success("Session created");
    return { ...result, description: result.description || void 0 };
  }
  async function getSession(sessionId) {
    return apiFetch(`/sessions/${sessionId}`);
  }
  async function getContainer(containerType, instanceId) {
    return apiFetch(`/containers/${containerType}/${instanceId}`);
  }
  async function updateContainer(containerType, instanceId, request) {
    return apiFetch(`/containers/${containerType}/${instanceId}`, {
      method: "PATCH",
      body: JSON.stringify(request)
    });
  }
  async function listContainerResources(containerType, instanceId, resourceType) {
    const params = resourceType ? `?resource_type=${resourceType}` : "";
    const response = await apiFetch(
      `/containers/${containerType}/${instanceId}/resources${params}`
    );
    return response.resources;
  }
  async function updateContainerResource(containerType, instanceId, linkId, request) {
    return apiFetch(
      `/containers/${containerType}/${instanceId}/resources/${linkId}`,
      {
        method: "PATCH",
        body: JSON.stringify(request)
      }
    );
  }
  async function removeContainerResource(containerType, instanceId, linkId) {
    await apiFetch(
      `/containers/${containerType}/${instanceId}/resources/${linkId}`,
      { method: "DELETE" }
    );
  }
  async function addAgentToSession(sessionId, agentDefinitionId, options) {
    const token = getAuthToken();
    const response = await fetch(`${API_URL}/sessions/${sessionId}/resources`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${token}`
      },
      body: JSON.stringify({
        resource_type: "agent",
        resource_id: agentDefinitionId,
        description: options?.description,
        preset_params: options?.preset_params || {},
        metadata: options?.metadata || {}
      })
    });
    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || "Failed to add agent");
    }
    toast.success("Agent added to session");
    return response.json();
  }
  async function addToolToSession(sessionId, toolDefinitionId, options) {
    const token = getAuthToken();
    const response = await fetch(`${API_URL}/sessions/${sessionId}/resources`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${token}`
      },
      body: JSON.stringify({
        resource_type: "tool",
        resource_id: toolDefinitionId,
        description: options?.description,
        preset_params: options?.preset_params || {},
        metadata: options?.metadata || {}
      })
    });
    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || "Failed to add tool");
    }
    toast.success("Tool added to session");
    return response.json();
  }
  async function addSourceToSession(sessionId, sourceDefinitionId, options) {
    const token = getAuthToken();
    const response = await fetch(`${API_URL}/sessions/${sessionId}/resources`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${token}`
      },
      body: JSON.stringify({
        resource_type: "source",
        resource_id: sourceDefinitionId,
        description: options?.description,
        preset_params: options?.preset_params || {},
        metadata: options?.metadata || {}
      })
    });
    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || "Failed to add source");
    }
    toast.success("Source added to session");
    return response.json();
  }
  async function addSessionResource(sessionId, request) {
    return apiFetch(`/sessions/${sessionId}/resources`, {
      method: "POST",
      body: JSON.stringify(request)
    });
  }
  async function listSessionResources(sessionId, resourceType) {
    const params = resourceType ? `?resource_type=${resourceType}` : "";
    const response = await apiFetch(
      `/sessions/${sessionId}/resources${params}`
    );
    return response.resources;
  }
  async function updateSessionResource(sessionId, linkId, updates) {
    return apiFetch(`/sessions/${sessionId}/resources/${linkId}`, {
      method: "PATCH",
      body: JSON.stringify(updates)
    });
  }
  async function deleteSessionResource(sessionId, linkId) {
    await apiFetch(`/sessions/${sessionId}/resources/${linkId}`, {
      method: "DELETE"
    });
  }
  async function queryResources(scopeId, query, scopeType = "session") {
    return apiFetch(`/query/resources?scope_id=${scopeId}&scope_type=${scopeType}`, {
      method: "POST",
      body: JSON.stringify(query)
    });
  }
  async function executeBatchOperation(request) {
    return apiFetch("/query/batch", {
      method: "POST",
      body: JSON.stringify(request)
    });
  }

  // src/lib/workspace-store.ts
  var import_meta2 = {};
  var resolveUserTier = () => {
    const raw = (localStorage.getItem("user_tier") || localStorage.getItem("tier") || import_meta2.env.VITE_USER_TIER || import_meta2.env.VITE_TIER || "ENTERPRISE").toString().toUpperCase();
    if (raw.includes("FREE")) return "FREE";
    if (raw.includes("PRO")) return "PRO";
    if (raw.includes("ENTER")) return "ENTERPRISE";
    return raw;
  };
  var maxDepthForTier = (tier) => tier === "FREE" ? 2 : 4;
  var navDepthFromBreadcrumbs = (breadcrumbs) => Math.max(0, (breadcrumbs?.length || 1) - 1);
  var enforceTierDepth = (state, options) => {
    const tier = resolveUserTier();
    const maxDepth = maxDepthForTier(tier);
    const navDepth = navDepthFromBreadcrumbs(state.breadcrumbs);
    const isTerminal = options?.isTerminal ?? false;
    if (state.activeContainerType === "source") {
      toast.warning("Source containers are terminal. Only Users may be added here.");
      return { ok: false, reason: "source-terminal" };
    }
    if (!isTerminal && navDepth >= maxDepth) {
      toast.warning(`Depth limit reached for ${tier}. Terminals only at L${maxDepth}.`);
      return { ok: false, reason: "depth-limit" };
    }
    return { ok: true, navDepth, maxDepth, tier };
  };
  var useWorkspaceStore = create()(
    persist(
      (set, get) => ({
        // Initial state
        nodes: [],
        edges: [],
        containers: [],
        // RENAMED from sessions
        sessionDatasources: {},
        sessionACLs: {},
        viewport: { x: 0, y: 0, zoom: 1 },
        sessionViewports: {},
        visualMetadata: /* @__PURE__ */ new Map(),
        selectedNodeIds: [],
        selectedEdgeIds: [],
        marquee: {
          isActive: false,
          startPoint: null,
          currentPoint: null,
          selectedNodeIds: []
        },
        stagedOperations: [],
        pendingOperations: [],
        dragLocks: /* @__PURE__ */ new Map(),
        activeSessionId: null,
        editingSessionId: null,
        editingSessionTab: "details",
        // Custom tools & agents (user-level)
        userCustomTools: [],
        userCustomAgents: [],
        // Discovery caches (workspace-wide discovery)
        availableTools: [],
        availableAgents: [],
        toolsCache: null,
        agentsCache: null,
        // User identity & preferences
        userIdentity: null,
        // V4.0.0 Universal Object Model state
        userId: null,
        // The user_id (e.g., "user_enterprise") - used for API calls
        userSessionId: null,
        workspaceResources: [],
        agentDefinitions: [],
        toolDefinitions: [],
        sourceDefinitions: [],
        // V4 Navigation
        activeContainerId: null,
        activeContainerType: null,
        activeContainerResource: null,
        containerResources: [],
        breadcrumbs: [],
        // =========================================================================
        // Computed Selectors for Container Hierarchy
        // =========================================================================
        // Legacy alias: `sessions` → `containers` (backward compatibility)
        get sessions() {
          return get().containers;
        },
        // L0 sessions only (no parentSessionId)
        getRootContainers: () => {
          return get().containers.filter((c) => !c.parentSessionId);
        },
        // L1+ children of a specific parent
        getChildContainers: (parentId) => {
          return get().containers.filter((c) => c.parentSessionId === parentId);
        },
        // Filter by containerType (session, agent, tool, source)
        getContainersByType: (type) => {
          return get().containers.filter((c) => c.containerType === type);
        },
        // Get container at breadcrumb path
        getContainerAtPath: (breadcrumbs) => {
          if (breadcrumbs.length === 0) return void 0;
          const targetId = breadcrumbs[breadcrumbs.length - 1].id;
          return get().containers.find((c) => c.id === targetId);
        },
        // Node actions
        enqueuePendingOperation: (operation) => {
          const opId = typeof crypto !== "undefined" && crypto.randomUUID ? crypto.randomUUID() : generateId("pending_op");
          set((state) => ({
            pendingOperations: [
              ...state.pendingOperations,
              {
                id: opId,
                status: "pending",
                retries: 0,
                createdAt: (/* @__PURE__ */ new Date()).toISOString(),
                ...operation
              }
            ]
          }));
          return opId;
        },
        updatePendingOperation: (id, updates) => set((state) => ({
          pendingOperations: state.pendingOperations.map(
            (op) => op.id === id ? { ...op, ...updates } : op
          )
        })),
        removePendingOperation: (id) => set((state) => ({
          pendingOperations: state.pendingOperations.filter((op) => op.id !== id)
        })),
        addNode: (node) => set((state) => ({
          nodes: [...state.nodes, node]
        })),
        updateNode: (id, updates) => set((state) => ({
          nodes: state.nodes.map((node) => node.id === id ? { ...node, ...updates } : node)
        })),
        deleteNode: (id) => set((state) => ({
          nodes: state.nodes.filter((node) => node.id !== id),
          edges: state.edges.filter((edge) => edge.source !== id && edge.target !== id)
        })),
        deleteNodes: (ids) => set((state) => ({
          nodes: state.nodes.filter((node) => !ids.includes(node.id)),
          edges: state.edges.filter(
            (edge) => !ids.includes(edge.source) && !ids.includes(edge.target)
          ),
          containers: state.containers.filter((container) => !ids.includes(container.id))
        })),
        duplicateNode: (id, offset = { x: 30, y: 30 }) => set((state) => {
          const nodeToClone = state.nodes.find((node) => node.id === id);
          if (!nodeToClone) return state;
          const newNode = {
            ...nodeToClone,
            id: generateId(nodeToClone.type),
            position: {
              x: nodeToClone.position.x + offset.x,
              y: nodeToClone.position.y + offset.y
            }
          };
          return { nodes: [...state.nodes, newNode] };
        }),
        editNode: (id) => {
          const node = get().nodes.find((n) => n.id === id);
          console.log(`Edit mode for node: ${node?.data?.name || id})`);
        },
        updateNodePosition: (id, position) => {
          set((state2) => ({
            nodes: state2.nodes.map((node) => node.id === id ? { ...node, position } : node)
          }));
          const state = get();
          const { activeContainerId, activeContainerType, userId, containerResources, workspaceResources } = state;
          if (activeContainerId) {
            const resource = containerResources.find((r) => r.link_id === id || r.resource_id === id);
            if (resource) {
              const updatedResource = {
                ...resource,
                metadata: { ...resource.metadata, x: position.x, y: position.y }
              };
              set({
                containerResources: containerResources.map(
                  (r) => r.link_id === id || r.resource_id === id ? updatedResource : r
                )
              });
              const linkId = resource.link_id || id;
              if (activeContainerType === "session") {
                updateSessionResource(activeContainerId, linkId, {
                  metadata: { x: position.x, y: position.y }
                }).catch((err) => console.error("Failed to sync position (session):", err));
              } else if (activeContainerType === "agent" || activeContainerType === "tool" || activeContainerType === "source") {
                updateContainerResource(activeContainerType, activeContainerId, linkId, {
                  metadata: { x: position.x, y: position.y }
                }).catch((err) => console.error(`Failed to sync position (${activeContainerType}):`, err));
              }
              return;
            }
          } else if (userId) {
            const resource = workspaceResources.find((r) => r.link_id === id || r.resource_id === id);
            if (resource) {
              const updatedResource = {
                ...resource,
                metadata: { ...resource.metadata, x: position.x, y: position.y }
              };
              set({
                workspaceResources: workspaceResources.map(
                  (r) => r.link_id === id || r.resource_id === id ? updatedResource : r
                )
              });
              updateWorkspaceResource(userId, resource.link_id || id, {
                metadata: { x: position.x, y: position.y }
              }).catch((err) => console.error("Failed to sync position (workspace):", err));
              return;
            }
          }
        },
        setNodes: (nodes) => set({ nodes }),
        // Edge actions
        addEdge: (edge) => set((state) => ({
          edges: [...state.edges, edge]
        })),
        deleteEdge: (id) => set((state) => ({
          edges: state.edges.filter((edge) => edge.id !== id)
        })),
        setEdges: (edges) => set({ edges }),
        // Session actions (legacy names, operate on containers)
        addSession: (session) => set((state) => ({
          containers: [...state.containers, session],
          nodes: [
            ...state.nodes,
            {
              id: session.id,
              type: "session",
              position: session.position,
              data: { ...session },
              style: { width: session.size.width, height: session.size.height }
            }
          ]
        })),
        updateSession: (id, updates) => set((state) => ({
          containers: state.containers.map(
            (container) => container.id === id ? { ...container, ...updates } : container
          )
        })),
        updateSessionId: (oldId, newId) => set((state) => ({
          containers: state.containers.map((s) => s.id === oldId ? { ...s, id: newId } : s),
          activeSessionId: state.activeSessionId === oldId ? newId : state.activeSessionId
        })),
        deleteSession: async (sessionId) => {
          const state = get();
          const { activeContainerId, activeContainerType, userId, containerResources, workspaceResources } = state;
          set((state2) => ({
            containers: state2.containers.filter((s) => s.id !== sessionId),
            nodes: state2.nodes.filter((n) => n.id !== sessionId),
            activeSessionId: state2.activeSessionId === sessionId ? void 0 : state2.activeSessionId,
            // V4 Optimistic
            containerResources: state2.containerResources.filter((r) => r.link_id !== sessionId && r.resource_id !== sessionId),
            workspaceResources: state2.workspaceResources.filter((r) => r.link_id !== sessionId && r.resource_id !== sessionId)
          }));
          try {
            if (activeContainerId) {
              const resource = containerResources.find((r) => r.link_id === sessionId || r.resource_id === sessionId);
              if (resource && resource.link_id) {
                if (activeContainerType === "session") {
                  await deleteSessionResource(activeContainerId, resource.link_id);
                } else if (activeContainerType === "agent" || activeContainerType === "tool" || activeContainerType === "source") {
                  await removeContainerResource(activeContainerType, activeContainerId, resource.link_id);
                }
              }
            } else if (userId) {
              const resource = workspaceResources.find((r) => r.link_id === sessionId || r.resource_id === sessionId);
              if (resource && resource.link_id) {
                await removeWorkspaceResource(userId, resource.link_id);
              }
            }
          } catch (error) {
            console.error("Failed to delete session on backend:", error);
          }
        },
        setSessions: (containers) => set({ containers }),
        // Actions - Viewport
        setViewport: (viewport) => set({ viewport }),
        setSessionViewport: (sessionId, viewport) => set((state) => ({
          sessionViewports: { ...state.sessionViewports, [sessionId]: viewport }
        })),
        getSessionViewport: (sessionId) => get().sessionViewports[sessionId],
        // Drag lock actions
        acquireDragLock: (nodeId, userId) => {
          const existingLock = get().dragLocks.get(nodeId);
          if (existingLock && existingLock.userId !== userId) {
            const now = /* @__PURE__ */ new Date();
            const expiresAt = new Date(existingLock.expiresAt);
            if (now < expiresAt) {
              return false;
            }
          }
          const newLock = {
            nodeId,
            userId,
            timestamp: (/* @__PURE__ */ new Date()).toISOString(),
            expiresAt: new Date(Date.now() + 5e3).toISOString()
            // 5 second timeout
          };
          set((state) => ({
            dragLocks: new Map(state.dragLocks).set(nodeId, newLock)
          }));
          return true;
        },
        releaseDragLock: (nodeId) => set((state) => {
          const newLocks = new Map(state.dragLocks);
          newLocks.delete(nodeId);
          return { dragLocks: newLocks };
        }),
        checkDragLock: (nodeId) => {
          const lock = get().dragLocks.get(nodeId);
          if (!lock) return null;
          const now = /* @__PURE__ */ new Date();
          const expiresAt = new Date(lock.expiresAt);
          if (now > expiresAt) {
            get().releaseDragLock(nodeId);
            return null;
          }
          return lock;
        },
        // Visual control actions
        applyLayout: (_algorithm, nodeIds, spacing = 100) => {
          const nodes = get().nodes.filter((n) => nodeIds.includes(n.id));
          const radius = Math.max(spacing * nodes.length / (2 * Math.PI), 150);
          const angleStep = 2 * Math.PI / nodes.length;
          set((state) => ({
            nodes: state.nodes.map((node) => {
              if (!nodeIds.includes(node.id)) return node;
              const nodeIndex = nodeIds.indexOf(node.id);
              const angle = nodeIndex * angleStep;
              return {
                ...node,
                position: {
                  x: Math.cos(angle) * radius,
                  y: Math.sin(angle) * radius
                }
              };
            })
          }));
        },
        updateTheme: (theme) => {
          console.log("Theme updated:", theme);
          const { preset, primary_color, background_color, node_style } = theme;
          if (preset) {
            const themeMap = {
              ocean: { bg: "#0a192f", primary: "#64ffda", node: "rounded" },
              forest: { bg: "#1a2f1a", primary: "#90ee90", node: "soft" },
              sunset: { bg: "#2f1a0a", primary: "#ff7b54", node: "rounded" },
              professional: { bg: "#1e1e1e", primary: "#007acc", node: "sharp" },
              dark: { bg: "#0f172a", primary: "#3b82f6", node: "rounded" },
              light: { bg: "#f8fafc", primary: "#2563eb", node: "rounded" }
            };
            const selectedTheme = themeMap[preset] || themeMap.dark;
            document.documentElement.style.setProperty("--workspace-bg", selectedTheme.bg);
            document.documentElement.style.setProperty("--primary-color", selectedTheme.primary);
            console.log(`Applied theme preset: ${preset}`);
          }
          if (primary_color) {
            document.documentElement.style.setProperty("--primary-color", primary_color);
          }
          if (background_color) {
            document.documentElement.style.setProperty("--workspace-bg", background_color);
          }
          if (node_style) {
            console.log(`Node style set to: ${node_style}`);
          }
        },
        setActiveSessionId: (id) => set({ activeSessionId: id }),
        // Switch to session (with viewport move)
        setActiveSession: (id) => {
          set({ activeSessionId: id });
          const session = get().containers.find((s) => s.id === id);
          if (session) {
            console.log(`\u{1F441}\uFE0F Switched to Session: ${session.title} (${id})`);
            set({
              viewport: {
                x: -session.position.x + 150,
                y: -session.position.y + 100,
                zoom: 1
              }
            });
          }
        },
        // UI state actions
        setEditingSessionId: (id, tab = "details") => set({ editingSessionId: id, editingSessionTab: tab }),
        // Marquee actions
        startMarquee: (point) => set({ marquee: { isActive: true, startPoint: point, currentPoint: point, selectedNodeIds: [] } }),
        updateMarquee: (point) => set((state) => ({ marquee: { ...state.marquee, currentPoint: point } })),
        endMarquee: () => set((state) => ({ marquee: { ...state.marquee, isActive: false, startPoint: null, currentPoint: null } })),
        cancelMarquee: () => set((state) => ({ marquee: { ...state.marquee, isActive: false, startPoint: null, currentPoint: null, selectedNodeIds: [] } })),
        // Selection actions
        setSelectedNodes: (ids) => set({ selectedNodeIds: ids }),
        setSelectedEdges: (ids) => set({ selectedEdgeIds: ids }),
        clearSelection: () => set({ selectedNodeIds: [], selectedEdgeIds: [] }),
        // Utility
        reset: () => {
          set({
            nodes: [],
            edges: [],
            containers: [],
            viewport: { x: 0, y: 0, zoom: 1 },
            selectedNodeIds: [],
            selectedEdgeIds: [],
            dragLocks: /* @__PURE__ */ new Map(),
            stagedOperations: []
          });
        },
        clearAll: () => {
          localStorage.removeItem("workspace-storage");
          get().reset();
        },
        // V4.0.0 Universal Object Model Actions
        // V4 Navigation
        loadContainer: async (containerId) => {
          const mode = import_meta2.env.VITE_MODE || "unknown";
          if (mode === "demo") {
            console.log(`\u{1F3AE} Demo Mode: loadContainer(${containerId || "root"}) - no backend calls`);
            if (!containerId) {
              set({
                activeContainerId: null,
                activeContainerType: null,
                activeContainerResource: null,
                breadcrumbs: [{ id: "root", title: "Workspace", type: "session" }]
              });
            } else {
              const currentBreadcrumbs = get().breadcrumbs;
              const allContainers = get().containers;
              const nodes = get().nodes;
              const container = allContainers.find((c) => c.id === containerId);
              const node = nodes.find((n) => n.id === containerId);
              const containerTitle = container?.title || node?.data?.label || node?.data?.title || containerId;
              const existingIndex = currentBreadcrumbs.findIndex((b) => b.id === containerId);
              let newBreadcrumbs;
              if (existingIndex >= 0) {
                newBreadcrumbs = currentBreadcrumbs.slice(0, existingIndex + 1);
              } else {
                newBreadcrumbs = [
                  ...currentBreadcrumbs,
                  { id: containerId, title: containerTitle, type: "session" }
                ];
              }
              set({
                activeContainerId: containerId,
                activeContainerType: "session",
                activeContainerResource: null,
                breadcrumbs: newBreadcrumbs
              });
            }
            return;
          }
          if (!containerId) {
            console.error("\u{1F504} loadContainer: Loading Root (UserSession)...");
            let userId = localStorage.getItem("user_id");
            if (!userId) {
              const token = localStorage.getItem("auth_token");
              if (token) {
                try {
                  const payload = JSON.parse(atob(token.split(".")[1]));
                  userId = payload.sub || payload.email || payload.user_id;
                  if (userId) {
                    localStorage.setItem("user_id", userId);
                  }
                } catch (e) {
                  console.warn("Could not decode JWT token:", e);
                }
              }
            }
            if (!userId) {
              console.error("No user_id found - please log in");
              return;
            }
            try {
              console.error(`\u{1F504} loadContainer: Fetching user session for ${userId}...`);
              const userSession = await getUserSession(userId);
              console.error("\u2705 loadContainer: Got user session:", userSession);
              console.error(`\u{1F504} loadContainer: Fetching workspace resources for ${userId}...`);
              const resources = await listWorkspaceResources(userId);
              console.error(`\u2705 loadContainer: Got ${resources.length} workspace resources`);
              set({
                userId,
                // Store the actual user_id for API calls
                userSessionId: userSession.instance_id,
                workspaceResources: resources,
                containerResources: [],
                activeContainerId: null,
                activeContainerType: null,
                activeContainerResource: null,
                breadcrumbs: [{ id: "root", title: "Workspace", type: "session" }]
              });
              console.error("\u{1F504} loadContainer: Triggering loadSessionsFromBackend...");
              await get().loadSessionsFromBackend();
            } catch (error) {
              console.error("Failed to load user session:", error);
            }
            return;
          }
          try {
            const detectedType = getContainerTypeFromId(containerId);
            let containerTitle = containerId;
            const containerType = detectedType || "session";
            const workspaceResourceLinks = get().workspaceResources;
            const resourceLink = workspaceResourceLinks.find((r) => r.link_id === containerId);
            const actualResourceId = resourceLink?.resource_id || containerId;
            const localContainers = get().containers;
            const localContainer = localContainers.find((c) => c.id === containerId);
            if (localContainer?.title) {
              containerTitle = localContainer.title;
            }
            if (containerType === "session") {
              try {
                const session = await getSession(actualResourceId);
                containerTitle = session.title || containerTitle;
              } catch (e) {
                console.warn("Could not fetch session details:", e);
              }
            } else if (containerType === "agent" || containerType === "tool" || containerType === "source") {
              try {
                const container = await getContainer(containerType, actualResourceId);
                containerTitle = container.title || containerTitle;
              } catch (e) {
                console.warn(`Could not fetch ${containerType} container details:`, e);
              }
            }
            const currentBreadcrumbs = get().breadcrumbs;
            const existingIndex = currentBreadcrumbs.findIndex((b) => b.id === containerId);
            let newBreadcrumbs;
            if (existingIndex >= 0) {
              newBreadcrumbs = currentBreadcrumbs.slice(0, existingIndex + 1);
            } else {
              newBreadcrumbs = [
                ...currentBreadcrumbs,
                { id: containerId, title: containerTitle, type: containerType }
              ];
            }
            set({
              activeContainerId: containerId,
              activeContainerType: containerType,
              activeContainerResource: null,
              // TODO: Fetch if needed
              breadcrumbs: newBreadcrumbs
            });
            let resources = [];
            if (containerType === "session") {
              resources = await listSessionResources(actualResourceId);
            } else if (isContainerDiveable(containerType)) {
              resources = await listContainerResources(containerType, actualResourceId);
            }
            set({ containerResources: resources });
          } catch (error) {
            console.error(`Failed to load resources for ${containerId}:`, error);
            set({ containerResources: [] });
          }
        },
        loadUserSession: async (userId) => {
          try {
            const response = await getUserSession(userId);
            set({ userSessionId: response.instance_id });
          } catch (error) {
            console.error("Failed to load user session:", error);
            throw error;
          }
        },
        loadWorkspaceResources: async (userId) => {
          try {
            const resources = await listWorkspaceResources(userId);
            set({ workspaceResources: resources });
          } catch (error) {
            console.error("Failed to load workspace resources:", error);
            throw error;
          }
        },
        loadAgentDefinitions: async (options) => {
          try {
            const definitions = await listDefinitions("agent", options);
            set({ agentDefinitions: definitions });
          } catch (error) {
            console.error("Failed to load agent definitions:", error);
            throw error;
          }
        },
        loadToolDefinitions: async (options) => {
          try {
            const definitions = await listDefinitions("tool", options);
            set({ toolDefinitions: definitions });
          } catch (error) {
            console.error("Failed to load tool definitions:", error);
            throw error;
          }
        },
        loadSourceDefinitions: async (options) => {
          try {
            const definitions = await listDefinitions("source", options);
            set({ sourceDefinitions: definitions });
          } catch (error) {
            console.error("Failed to load source definitions:", error);
            throw error;
          }
        },
        addAgentToSessionV4: async (sessionId, agentDefinitionId, options) => {
          const state = get();
          const guard = enforceTierDepth({
            activeContainerType: state.activeContainerType,
            breadcrumbs: state.breadcrumbs
          }, { isTerminal: false });
          if (!guard.ok) {
            throw new Error(`Tier depth guard blocked addAgent: ${guard.reason}`);
          }
          const mode = import_meta2.env.VITE_MODE;
          if (mode === "demo") {
            console.log("\u{1F3AE} Demo Mode: addAgentToSession - local only", { sessionId, agentDefinitionId, options });
            const state2 = get();
            const nodeId = `agnt_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
            const position = options?.metadata || { x: 100, y: 100 };
            const newNode = {
              id: nodeId,
              type: "agent",
              position: { x: position.x ?? 100, y: position.y ?? 100 },
              data: {
                id: nodeId,
                type: "agent",
                label: options?.description || agentDefinitionId,
                sessionId,
                themeColor: "#8b5cf6",
                // Purple for agents
                definition_id: agentDefinitionId
              }
            };
            set({ nodes: [...state2.nodes, newNode] });
            return;
          }
          try {
            await addAgentToSession(sessionId, agentDefinitionId, options);
            const state2 = get();
            if (state2.activeContainerId === sessionId) {
              const resources = await listSessionResources(sessionId);
              set({ containerResources: resources });
            } else if (state2.userSessionId) {
              await get().loadWorkspaceResources(state2.userSessionId);
            }
          } catch (error) {
            console.error("Failed to add agent to session:", error);
            throw error;
          }
        },
        addToolToSessionV4: async (sessionId, toolDefinitionId, options) => {
          const state = get();
          const guard = enforceTierDepth({
            activeContainerType: state.activeContainerType,
            breadcrumbs: state.breadcrumbs
          }, { isTerminal: false });
          if (!guard.ok) {
            throw new Error(`Tier depth guard blocked addTool: ${guard.reason}`);
          }
          const mode = import_meta2.env.VITE_MODE;
          if (mode === "demo") {
            console.log("\u{1F3AE} Demo Mode: addToolToSession - local only", { sessionId, toolDefinitionId, options });
            const state2 = get();
            const nodeId = `tool_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
            const position = options?.metadata || { x: 100, y: 100 };
            const newNode = {
              id: nodeId,
              type: "tool",
              position: { x: position.x ?? 100, y: position.y ?? 100 },
              data: {
                id: nodeId,
                type: "tool",
                label: options?.description || toolDefinitionId,
                sessionId,
                themeColor: "#22c55e",
                // Green for tools
                category: "data",
                definition_id: toolDefinitionId
              }
            };
            set({ nodes: [...state2.nodes, newNode] });
            return;
          }
          try {
            await addToolToSession(sessionId, toolDefinitionId, options);
            const state2 = get();
            if (state2.activeContainerId === sessionId) {
              const resources = await listSessionResources(sessionId);
              set({ containerResources: resources });
            } else if (state2.userSessionId) {
              await get().loadWorkspaceResources(state2.userSessionId);
            }
          } catch (error) {
            console.error("Failed to add tool to session:", error);
            throw error;
          }
        },
        addSourceToSessionV4: async (sessionId, sourceDefinitionId, options) => {
          const state = get();
          const guard = enforceTierDepth({
            activeContainerType: state.activeContainerType,
            breadcrumbs: state.breadcrumbs
          }, { isTerminal: true });
          if (!guard.ok) {
            throw new Error(`Tier depth guard blocked addSource: ${guard.reason}`);
          }
          const mode = import_meta2.env.VITE_MODE;
          if (mode === "demo") {
            console.log("\u{1F3AE} Demo Mode: addSourceToSession - local only", { sessionId, sourceDefinitionId, options });
            const state2 = get();
            const nodeId = `source_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
            const position = options?.metadata || { x: 100, y: 100 };
            const newNode = {
              id: nodeId,
              type: "source",
              position: { x: position.x ?? 100, y: position.y ?? 100 },
              data: {
                linkId: nodeId,
                resourceId: sourceDefinitionId,
                resourceType: "source",
                title: options?.description || sourceDefinitionId,
                description: options?.description,
                enabled: true,
                presetParams: options?.preset_params || {},
                inputMappings: {},
                metadata: {
                  ...options?.metadata || {},
                  x: position.x ?? 100,
                  y: position.y ?? 100,
                  sessionId
                }
              }
            };
            set({ nodes: [...state2.nodes, newNode] });
            return;
          }
          try {
            await addSourceToSession(sessionId, sourceDefinitionId, options);
            const state2 = get();
            if (state2.activeContainerId === sessionId) {
              const resources = await listSessionResources(sessionId);
              set({ containerResources: resources });
            } else if (state2.userSessionId) {
              await get().loadWorkspaceResources(state2.userSessionId);
            }
          } catch (error) {
            console.error("Failed to add source to session:", error);
            throw error;
          }
        },
        /**
         * Update a ResourceLink (Quick Edit for containers)
         * 
         * This updates the ResourceLink document in the parent container's subcollection.
         * The nodeId can be either the link_id or resource_id (both are checked).
         * 
         * Updates flow:
         * 1. Optimistically update Zustand state (nodes + resources arrays)
         * 2. Call appropriate API based on context (workspace root vs inside container)
         * 
         * @param nodeId - The ReactFlow node ID (which is link_id or resource_id)
         * @param updates - ResourceLink fields to update (description, preset_params, metadata, enabled)
         */
        updateContainer: async (containerType, containerId, updates) => {
          const mode = import_meta2.env.VITE_MODE || "unknown";
          if (mode === "demo") {
            console.log("\u{1F3AE} Demo Mode: updateContainer - local only", { containerType, containerId, updates });
            set((state) => ({
              nodes: state.nodes.map((n) => {
                const data = n.data;
                if (n.id === containerId || data.resource_id === containerId || data.id === containerId) {
                  return {
                    ...n,
                    data: {
                      ...data,
                      title: updates.title ?? data.title,
                      description: updates.description ?? data.description
                    }
                  };
                }
                return n;
              })
            }));
            return;
          }
          try {
            if (containerType === "session") {
              console.warn("Backend update for session not supported yet via API");
            } else {
              await updateContainer(containerType, containerId, updates);
            }
            set((state) => ({
              nodes: state.nodes.map((n) => {
                const data = n.data;
                if (data.resource_id === containerId) {
                  return {
                    ...n,
                    data: {
                      ...data,
                      title: updates.title ?? data.title
                    }
                  };
                }
                return n;
              })
            }));
          } catch (error) {
            console.error("Failed to update container:", error);
            throw error;
          }
        },
        updateResourceLink: async (nodeId, updates) => {
          const state = get();
          const { activeContainerId, activeContainerType, userId, containerResources, workspaceResources, nodes } = state;
          const mode = import_meta2.env.VITE_MODE || "unknown";
          if (mode === "demo") {
            console.log("\u{1F3AE} Demo Mode: updateResourceLink - local only", { nodeId, updates });
            set({
              nodes: nodes.map((n) => {
                if (n.id !== nodeId) return n;
                const nodeData = n.data;
                return {
                  ...n,
                  data: {
                    ...nodeData,
                    enabled: updates.enabled ?? nodeData.enabled,
                    presetParams: updates.preset_params ? { ...nodeData.presetParams || {}, ...updates.preset_params } : nodeData.presetParams,
                    metadata: updates.metadata ? { ...nodeData.metadata || {}, ...updates.metadata } : nodeData.metadata,
                    // Also update legacy fields
                    themeColor: updates.metadata?.color || nodeData.themeColor
                  }
                };
              })
            });
            return;
          }
          let resource;
          let isWorkspaceRoot = false;
          if (activeContainerId) {
            resource = containerResources.find((r) => r.link_id === nodeId || r.resource_id === nodeId);
          } else if (userId) {
            resource = workspaceResources.find((r) => r.link_id === nodeId || r.resource_id === nodeId);
            isWorkspaceRoot = true;
          }
          if (!resource) {
            console.error("ResourceLink not found for nodeId:", nodeId);
            return;
          }
          const linkId = resource.link_id || nodeId;
          const updatedResource = {
            ...resource,
            preset_params: updates.preset_params ? { ...resource.preset_params, ...updates.preset_params } : resource.preset_params,
            metadata: updates.metadata ? { ...resource.metadata, ...updates.metadata } : resource.metadata,
            enabled: updates.enabled ?? resource.enabled
          };
          if (isWorkspaceRoot) {
            set({
              workspaceResources: workspaceResources.map(
                (r) => r.link_id === nodeId || r.resource_id === nodeId ? updatedResource : r
              )
            });
          } else {
            set({
              containerResources: containerResources.map(
                (r) => r.link_id === nodeId || r.resource_id === nodeId ? updatedResource : r
              )
            });
          }
          set({
            nodes: nodes.map((n) => {
              if (n.id !== nodeId) return n;
              const nodeData = n.data;
              return {
                ...n,
                data: {
                  ...nodeData,
                  enabled: updates.enabled ?? nodeData.enabled,
                  presetParams: updates.preset_params ? { ...nodeData.presetParams || {}, ...updates.preset_params } : nodeData.presetParams,
                  metadata: updates.metadata ? { ...nodeData.metadata || {}, ...updates.metadata } : nodeData.metadata,
                  // Also update legacy fields
                  themeColor: updates.metadata?.color || nodeData.themeColor
                }
              };
            })
          });
          try {
            if (isWorkspaceRoot && userId) {
              await updateWorkspaceResource(userId, linkId, updates);
            } else if (activeContainerId) {
              if (activeContainerType === "session") {
                await updateSessionResource(activeContainerId, linkId, updates);
              } else if (activeContainerType === "agent" || activeContainerType === "tool" || activeContainerType === "source") {
                await updateContainerResource(activeContainerType, activeContainerId, linkId, updates);
              }
            }
            console.log("\u2705 ResourceLink updated:", linkId);
          } catch (error) {
            console.error("\u274C Failed to update ResourceLink:", error);
            throw error;
          }
        },
        // Staging Queue actions
        addStagedOperation: (operation) => set((state) => ({
          stagedOperations: [
            ...state.stagedOperations,
            {
              ...operation,
              id: generateId("op"),
              timestamp: (/* @__PURE__ */ new Date()).toISOString(),
              status: "pending"
            }
          ]
        })),
        removeStagedOperation: (id) => set((state) => ({
          stagedOperations: state.stagedOperations.filter((op) => op.id !== id)
        })),
        updateStagedOperation: (id, updates) => set((state) => ({
          stagedOperations: state.stagedOperations.map(
            (op) => op.id === id ? { ...op, ...updates } : op
          )
        })),
        executeStagedOperations: async () => {
          const operations = get().stagedOperations.filter((op) => op.status === "pending");
          if (operations.length === 0) {
            console.log("No pending operations to execute");
            return;
          }
          console.warn("Staged operations are deprecated in V4. Clearing queue.");
          get().clearStagedOperations();
        },
        clearStagedOperations: () => set({ stagedOperations: [] }),
        // AI-Driven Selection actions
        selectNodesByType: (type) => {
          const nodeIds = get().nodes.filter((n) => n.type === type).map((n) => n.id);
          set({ selectedNodeIds: nodeIds });
          console.log(`\u{1F3AF} Selected ${nodeIds.length} nodes of type "${type}"`);
        },
        selectNodesByTag: (tag) => {
          const nodeIds = get().nodes.filter((n) => {
            const data = n.data;
            return data?.data?.tags?.includes(tag);
          }).map((n) => n.id);
          set({ selectedNodeIds: nodeIds });
          console.log(`\u{1F3F7}\uFE0F Selected ${nodeIds.length} nodes with tag "${tag}"`);
        },
        selectAllNodes: () => {
          const nodeIds = get().nodes.map((n) => n.id);
          set({ selectedNodeIds: nodeIds });
          console.log(`\u{1F4E6} Selected all ${nodeIds.length} nodes`);
        },
        // Custom Tools: User-level CRUD
        loadUserCustomTools: async () => {
          try {
            const definitions = await listDefinitions("tool");
            const tools = definitions.map((d) => ({
              tool_id: d.definition_id,
              user_id: "current_user",
              name: d.title,
              description: d.description || "",
              type: "builtin",
              builtin_tool_name: d.spec?.builtin_tool_name || "unknown",
              config: d.spec?.config || {},
              tags: d.tags || [],
              created_at: d.created_at,
              updated_at: d.updated_at,
              tier_required: d.tier
            }));
            set({ userCustomTools: tools });
            console.log(`\u2705 Loaded ${tools.length} user custom tools`);
          } catch (error) {
            console.error("Failed to load user custom tools:", error);
            set({ userCustomTools: [] });
          }
        },
        createUserCustomTool: async (payload) => {
          const request = {
            title: payload.name,
            description: payload.description,
            spec: {
              builtin_tool_name: payload.builtin_tool_name,
              config: payload.config
            },
            tags: payload.tags || []
          };
          const d = await createDefinition("tool", request);
          const tool = {
            tool_id: d.definition_id,
            user_id: "current_user",
            name: d.title,
            description: d.description || "",
            type: "builtin",
            builtin_tool_name: payload.builtin_tool_name,
            config: payload.config,
            tags: d.tags || [],
            created_at: d.created_at,
            updated_at: d.updated_at,
            tier_required: d.tier
          };
          set((state) => ({
            userCustomTools: [...state.userCustomTools, tool]
          }));
          return tool;
        },
        deleteUserCustomTool: async (toolId) => {
          await deleteDefinition("tool", toolId);
          set((state) => ({
            userCustomTools: state.userCustomTools.filter((t) => t.tool_id !== toolId)
          }));
        },
        // Custom Agents: User-level CRUD
        loadUserCustomAgents: async () => {
          try {
            const definitions = await listDefinitions("agent");
            const agents = definitions.map((d) => ({
              agent_id: d.definition_id,
              user_id: "current_user",
              name: d.title,
              description: d.description || "",
              system_prompt: d.spec?.system_prompt || "",
              model: d.spec?.model,
              tags: d.tags || [],
              created_at: d.created_at,
              updated_at: d.updated_at,
              tier_required: d.tier
            }));
            set({ userCustomAgents: agents });
            console.log(`\u2705 Loaded ${agents.length} user custom agents`);
          } catch (error) {
            console.error("Failed to load user custom agents:", error);
            set({ userCustomAgents: [] });
          }
        },
        createUserCustomAgent: async (payload) => {
          const request = {
            title: payload.name,
            description: payload.description,
            spec: {
              system_prompt: payload.system_prompt,
              model: payload.model
            },
            tags: payload.tags || []
          };
          const d = await createDefinition("agent", request);
          const agent = {
            agent_id: d.definition_id,
            user_id: "current_user",
            name: d.title,
            description: d.description || "",
            system_prompt: payload.system_prompt,
            model: payload.model,
            tags: d.tags || [],
            created_at: d.created_at,
            updated_at: d.updated_at,
            tier_required: d.tier
          };
          set((state) => ({
            userCustomAgents: [...state.userCustomAgents, agent]
          }));
          return agent;
        },
        updateUserCustomAgent: async (agentId, payload) => {
          const request = {};
          if (payload.name) request.title = payload.name;
          if (payload.description) request.description = payload.description;
          if (payload.tags) request.tags = payload.tags;
          if (payload.system_prompt || payload.model) {
            request.spec = {};
            if (payload.system_prompt) request.spec.system_prompt = payload.system_prompt;
            if (payload.model) request.spec.model = payload.model;
          }
          const d = await updateDefinition("agent", agentId, request);
          const agent = {
            agent_id: d.definition_id,
            user_id: "current_user",
            name: d.title,
            description: d.description || "",
            system_prompt: d.spec?.system_prompt || "",
            model: d.spec?.model,
            tags: d.tags || [],
            created_at: d.created_at,
            updated_at: d.updated_at,
            tier_required: d.tier
          };
          set((state) => ({
            userCustomAgents: state.userCustomAgents.map(
              (a) => a.agent_id === agentId ? agent : a
            )
          }));
          return agent;
        },
        deleteUserCustomAgent: async (agentId) => {
          await deleteDefinition("agent", agentId);
          set((state) => ({
            userCustomAgents: state.userCustomAgents.filter((a) => a.agent_id !== agentId)
          }));
        },
        // Session Tool Instances: Session-scoped tool usage - REMOVED (Legacy V3)
        // Session Agent Instances: Session-scoped agent usage - REMOVED (Legacy V3)
        addSessionDatasource: async (sessionId, payload) => {
          throw new Error("Legacy addSessionDatasource called. Use addSourceToSessionV4 instead.");
        },
        updateSessionDatasource: async (sessionId, attachmentId, payload) => {
          throw new Error("Legacy updateSessionDatasource called. Use updateSessionResource instead.");
        },
        removeSessionDatasource: async (sessionId, attachmentId) => {
          throw new Error("Legacy removeSessionDatasource called. Use deleteSessionResource instead.");
        },
        addSessionACL: async (sessionId, payload) => {
          throw new Error("Legacy addSessionACL called. Use addSessionResource (user) instead.");
        },
        updateSessionACL: async (sessionId, aclId, payload) => {
          throw new Error("Legacy updateSessionACL called. Use updateSessionResource instead.");
        },
        removeSessionACL: async (sessionId, aclId) => {
          throw new Error("Legacy removeSessionACL called. Use deleteSessionResource instead.");
        },
        createContainer: async (title, parentSessionId, nodeIds) => {
          const session = await createSession({
            title,
            parent_session_id: parentSessionId,
            metadata: { nodeIds }
          });
          return {
            id: session.session_id,
            type: "container",
            position: { x: 0, y: 0 },
            data: { ...session }
          };
        },
        createChildSession: async (parentSessionId, title, position, description) => {
          const store = get();
          const guard = enforceTierDepth({
            activeContainerType: store.activeContainerType,
            breadcrumbs: store.breadcrumbs
          }, { isTerminal: false });
          if (!guard.ok) {
            throw new Error(`Tier depth guard blocked createChildSession: ${guard.reason}`);
          }
          if (store.userSessionId || store.activeContainerId) {
            try {
              const isWorkspaceParent = store.userSessionId === parentSessionId;
              const newSession2 = await createSession({
                title,
                description: description || "",
                // For nested sessions, attach parent_session_id for depth computation
                parent_session_id: isWorkspaceParent ? void 0 : parentSessionId
              });
              if (isWorkspaceParent && store.userSessionId) {
                await addWorkspaceResource(store.userSessionId, {
                  resource_type: "session",
                  resource_id: newSession2.session_id,
                  description: newSession2.description,
                  metadata: {
                    x: position?.x || 0,
                    y: position?.y || 0
                  }
                });
                await store.loadWorkspaceResources(store.userSessionId);
              } else {
                await addSessionResource(parentSessionId, {
                  resource_type: "session",
                  resource_id: newSession2.session_id,
                  description: newSession2.description,
                  metadata: {
                    x: position?.x || 0,
                    y: position?.y || 0
                  }
                });
                await store.loadContainer(parentSessionId);
              }
              return {
                id: newSession2.session_id,
                title: newSession2.title,
                position: position || { x: 0, y: 0 },
                size: { width: 280, height: 180 },
                type: "session",
                data: { ...newSession2 }
              };
            } catch (error) {
              console.warn("\u26A0\uFE0F API creation failed, falling back to local (Demo Mode):", error);
            }
          }
          const newSession = {
            id: `session-${Date.now()}`,
            title,
            position: position || { x: 0, y: 0 },
            size: { width: 280, height: 180 },
            type: "session",
            containerType: "session",
            data: { label: title, description },
            parentSessionId
          };
          set((state) => ({
            containers: [...state.containers, newSession],
            nodes: [...state.nodes, {
              id: newSession.id,
              type: "session",
              position: newSession.position,
              data: { ...newSession },
              style: { width: newSession.size.width, height: newSession.size.height }
            }]
          }));
          return newSession;
        },
        // Query & Batch Actions (V4.1)
        findResources: async (scopeId, query, scopeType = "session") => {
          try {
            return await queryResources(scopeId, query, scopeType);
          } catch (error) {
            console.error("Failed to find resources:", error);
            toast.error("Search failed");
            throw error;
          }
        },
        batchDeleteResources: async (items) => {
          try {
            const result = await executeBatchOperation({
              operation: "delete",
              items
            });
            if (result.failure_count > 0) {
              toast.warning(`Batch delete: ${result.success_count} success, ${result.failure_count} failed`);
            } else {
              toast.success(`Deleted ${result.success_count} items`);
            }
            const state = get();
            const currentId = state.activeContainerId || state.userSessionId;
            if (currentId && items.some((i) => i.parent_id === currentId)) {
              await get().loadContainer(currentId);
            }
            return result;
          } catch (error) {
            console.error("Batch delete failed:", error);
            toast.error("Batch operation failed");
            throw error;
          }
        },
        setVisualMetadata: (sessionId, metadata) => {
          set((state) => {
            const newMap = new Map(state.visualMetadata);
            newMap.set(sessionId, metadata);
            return { visualMetadata: newMap };
          });
        },
        updateVisualMetadata: (sessionId, updates) => {
          set((state) => {
            const newMap = new Map(state.visualMetadata);
            const existing = newMap.get(sessionId) || {
              position: { x: 0, y: 0 },
              size: { width: 0, height: 0 },
              color: "",
              collapsed: false,
              is_container: false
            };
            newMap.set(sessionId, { ...existing, ...updates });
            return { visualMetadata: newMap };
          });
        },
        getVisualMetadata: (sessionId) => {
          return get().visualMetadata.get(sessionId);
        },
        loadSessionsFromBackend: async () => {
          const state = get();
          console.error("\u{1F504} loadSessionsFromBackend: Starting...", {
            activeContainerId: state.activeContainerId,
            workspaceResourcesLen: state.workspaceResources.length,
            containerResourcesLen: state.containerResources.length
          });
          const resources = state.activeContainerId ? state.containerResources : state.workspaceResources;
          const sessionResources = resources.filter((r) => r.resource_type === "session");
          console.error(`\u{1F504} loadSessionsFromBackend: Found ${sessionResources.length} session resources out of ${resources.length} total`);
          set((state2) => {
            const mappedContainers = sessionResources.map((r) => ({
              id: r.link_id || r.resource_id,
              title: r.description || "Session",
              position: { x: r.metadata?.x || 100, y: r.metadata?.y || 100 },
              size: { width: 280, height: 180 },
              // Default size
              themeColor: "blue",
              status: "active",
              expanded: true,
              description: r.description,
              tags: [],
              containerType: "session",
              sessionType: "chat",
              // Default
              createdAt: r.added_at,
              updatedAt: r.added_at,
              metadata: r.metadata
            }));
            const nonSessionNodes = state2.nodes.filter((n) => n.type !== "session");
            const sessionNodes = mappedContainers.map((s) => ({
              id: s.id,
              type: "session",
              position: s.position,
              data: { ...s },
              style: { width: s.size.width, height: s.size.height }
            }));
            console.error(`\u2705 loadSessionsFromBackend: Updating nodes. New count: ${nonSessionNodes.length + sessionNodes.length} (${sessionNodes.length} sessions)`);
            return {
              containers: mappedContainers,
              nodes: [...nonSessionNodes, ...sessionNodes]
            };
          });
          console.error("\u2705 Synced containers from V4 resources");
        },
        loadSessionDatasources: async (sessionId) => {
        },
        loadSessionACLs: async (sessionId) => {
        },
        // Tool Discovery: Browse available system + custom tools (with caching)
        loadAvailableTools: async (category, forceRefresh = false) => {
          const cache = get().toolsCache;
          const CACHE_DURATION_MS = 5 * 60 * 1e3;
          if (!forceRefresh && cache && Date.now() - cache.timestamp < CACHE_DURATION_MS && cache.category === category) {
            console.log("\u2705 Using cached available tools");
            return;
          }
          try {
            const definitions = await listDefinitions("tool");
            const tools = definitions.map((d) => ({
              tool_id: d.definition_id,
              name: d.name,
              description: d.description,
              category: "general",
              // Default
              version: d.version,
              parameters: d.schema?.parameters || {}
            }));
            set({
              availableTools: tools,
              // Cast to satisfy legacy type
              toolsCache: { timestamp: Date.now(), category }
            });
            console.log(`\u2705 Loaded ${tools.length} available tools (V4)`);
          } catch (error) {
            console.error("Failed to load available tools:", error);
            set({ availableTools: [] });
          }
        },
        loadToolDetails: async (toolName) => {
          const tool = get().availableTools.find((t) => t.name === toolName);
          return tool;
        },
        // Agent Discovery: Browse available system + custom agents (with caching)
        loadAvailableAgents: async (sessionId, search, forceRefresh = false) => {
          const cache = get().agentsCache;
          const CACHE_DURATION_MS = 5 * 60 * 1e3;
          if (!forceRefresh && cache && Date.now() - cache.timestamp < CACHE_DURATION_MS && cache.sessionId === sessionId && cache.search === search) {
            console.log("\u2705 Using cached available agents");
            return;
          }
          try {
            const definitions = await listDefinitions("agent");
            const agents = definitions.map((d) => ({
              agent_id: d.definition_id,
              name: d.name,
              description: d.description,
              capabilities: [],
              version: d.version
            }));
            set({
              availableAgents: agents,
              // Cast to satisfy legacy type
              agentsCache: { timestamp: Date.now(), sessionId, search }
            });
            console.log(`\u2705 Loaded ${agents.length} available agents (V4)`);
          } catch (error) {
            console.error("Failed to load available agents:", error);
            set({ availableAgents: [] });
          }
        },
        loadAgentDetails: async (agentId) => {
          const d = await getDefinition("agent", agentId);
          const details = {
            agent_id: d.definition_id,
            name: d.title,
            description: d.description || "",
            capabilities: [],
            version: d.version
          };
          set((state) => ({
            availableAgents: state.availableAgents.map(
              (a) => a.agent_id === agentId ? { ...a, ...details } : a
            )
          }));
          return details;
        }
      }),
      {
        name: "workspace-storage",
        partialize: (state) => ({
          nodes: state.nodes,
          edges: state.edges,
          containers: state.containers,
          viewport: state.viewport,
          sessionViewports: state.sessionViewports,
          visualMetadata: Array.from(state.visualMetadata.entries()),
          // Serialize Map
          sessionDatasources: state.sessionDatasources,
          sessionACLs: state.sessionACLs,
          // Custom tools & agents (user-level)
          userCustomTools: state.userCustomTools,
          userCustomAgents: state.userCustomAgents,
          // Session instances (session-scoped tools/agents)
          sessionToolInstances: state.sessionToolInstances,
          sessionAgentInstances: state.sessionAgentInstances,
          // Discovery caches (for fast reload)
          availableTools: state.availableTools,
          availableAgents: state.availableAgents,
          toolsCache: state.toolsCache,
          agentsCache: state.agentsCache
        }),
        onRehydrateStorage: () => (state) => {
          if (typeof window !== "undefined") {
            try {
              const raw = localStorage.getItem("workspace-storage");
              if (raw) {
                const parsed = JSON.parse(raw);
                const storedState = parsed.state || parsed;
                if (storedState.sessions && !storedState.containers) {
                  console.warn("\u26A0\uFE0F Detected old sessions[] schema - clearing for migration");
                  localStorage.removeItem("workspace-storage");
                  window.location.reload();
                  return;
                }
              }
            } catch (e) {
              console.warn("Failed to check localStorage schema:", e);
            }
          }
          if (state && state.visualMetadata) {
            state.visualMetadata = new Map(state.visualMetadata);
          }
          const mode = import_meta2.env.VITE_MODE || "demo";
          if (state && mode !== "demo") {
            state.nodes = [];
            state.edges = [];
            state.containers = [];
            state.sessionDatasources = {};
            state.sessionACLs = {};
            state.visualMetadata = /* @__PURE__ */ new Map();
          }
          if (typeof window !== "undefined") {
            let isLocalWrite = false;
            const originalSetState = useWorkspaceStore.setState;
            useWorkspaceStore.setState = (...args) => {
              isLocalWrite = true;
              originalSetState(...args);
              setTimeout(() => {
                isLocalWrite = false;
              }, 100);
            };
            window.addEventListener("storage", (e) => {
              if (e.key === "workspace-storage" && e.newValue && !isLocalWrite) {
                console.log("\u{1F504} Cross-tab sync: loading changes from another tab");
                try {
                  const data = JSON.parse(e.newValue);
                  const state2 = data.state || data;
                  originalSetState(state2);
                } catch (error) {
                  console.error("Failed to sync cross-tab localStorage change:", error);
                }
              }
            });
          }
        }
      }
    )
  );
  var getSessionLevel = (sessionId) => {
    const containers = useWorkspaceStore.getState().containers;
    let level = 0;
    let current = containers.find((c) => c.id === sessionId);
    while (current?.parentSessionId) {
      level++;
      current = containers.find((c) => c.id === current.parentSessionId);
      if (level > 10) {
        console.warn(`\u26A0\uFE0F Session ${sessionId} has suspiciously deep nesting (>10 levels)`);
        break;
      }
    }
    return level;
  };
  var getSessionPath = (sessionId) => {
    const containers = useWorkspaceStore.getState().containers;
    const path = [];
    let current = containers.find((c) => c.id === sessionId);
    while (current) {
      path.unshift(current.id);
      current = current.parentSessionId ? containers.find((c) => c.id === current.parentSessionId) : void 0;
      if (path.length > 10) break;
    }
    return path;
  };
  if (typeof window !== "undefined") {
    window.__ZUSTAND_STORE__ = useWorkspaceStore;
  }
})();
/*! Bundled license information:

react/cjs/react.development.js:
  (**
   * @license React
   * react.development.js
   *
   * Copyright (c) Facebook, Inc. and its affiliates.
   *
   * This source code is licensed under the MIT license found in the
   * LICENSE file in the root directory of this source tree.
   *)
*/
